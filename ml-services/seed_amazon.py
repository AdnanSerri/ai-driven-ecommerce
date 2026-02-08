#!/usr/bin/env python3
"""
Seed PostgreSQL with real Amazon Reviews 2023 data from HuggingFace.

Downloads product metadata and reviews from McAuley-Lab/Amazon-Reviews-2023,
then generates synthetic orders, addresses, wishlists, carts, and user
interactions shaped by personality archetypes for ML training.

Usage:
    python seed_amazon.py                          # Default settings
    python seed_amazon.py --max-products 500       # Fewer products
    python seed_amazon.py --placeholder-images     # Use placeholder URLs
    python seed_amazon.py --dry-run                # Preview without inserting
"""

import argparse
import asyncio
import json
import os
import random
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import asyncpg
import bcrypt
from dotenv import load_dotenv
from faker import Faker

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CATEGORIES = [
    "Electronics",
    "Books",
    "Home_and_Kitchen",
    "Clothing_Shoes_and_Jewelry",
    "Sports_and_Outdoors",
]

# Sub-categories per main category (used when Amazon data lacks breadcrumbs)
DEFAULT_SUBCATEGORIES = {
    "Electronics": [
        "Smartphones", "Laptops", "Headphones", "Cameras", "Tablets",
        "Wearables", "Speakers", "Accessories",
    ],
    "Books": [
        "Fiction", "Non-Fiction", "Science", "Technology", "Self-Help",
        "Biography", "History", "Children",
    ],
    "Home_and_Kitchen": [
        "Kitchen Appliances", "Furniture", "Bedding", "Storage",
        "Lighting", "Cookware", "Decor",
    ],
    "Clothing_Shoes_and_Jewelry": [
        "Men's Clothing", "Women's Clothing", "Shoes", "Jewelry",
        "Accessories", "Watches", "Activewear",
    ],
    "Sports_and_Outdoors": [
        "Fitness Equipment", "Outdoor Recreation", "Team Sports",
        "Water Sports", "Camping", "Cycling", "Running",
    ],
}

# Price ranges for fallback generation (min, max)
CATEGORY_PRICE_RANGES = {
    "Electronics": (15.0, 999.0),
    "Books": (5.0, 45.0),
    "Home_and_Kitchen": (10.0, 350.0),
    "Clothing_Shoes_and_Jewelry": (8.0, 250.0),
    "Sports_and_Outdoors": (10.0, 400.0),
}

PERSONALITY_ARCHETYPES = {
    "ADVENTUROUS_PREMIUM": {
        "avg_view_duration": 15,
        "view_duration_std": 8,
        "categories_explored": (4, 5),
        "views_per_purchase": (3, 6),
        "price_preference": "high",
        "purchase_frequency": "moderate",
    },
    "CAUTIOUS_VALUE_SEEKER": {
        "avg_view_duration": 240,
        "view_duration_std": 60,
        "categories_explored": (1, 2),
        "views_per_purchase": (10, 20),
        "price_preference": "low",
        "purchase_frequency": "low",
    },
    "LOYAL_ENTHUSIAST": {
        "avg_view_duration": 60,
        "view_duration_std": 20,
        "categories_explored": (1, 3),
        "views_per_purchase": (4, 8),
        "price_preference": "moderate",
        "purchase_frequency": "high",
    },
    "BARGAIN_HUNTER": {
        "avg_view_duration": 30,
        "view_duration_std": 15,
        "categories_explored": (3, 5),
        "views_per_purchase": (8, 15),
        "price_preference": "low",
        "purchase_frequency": "moderate",
    },
    "QUALITY_FOCUSED": {
        "avg_view_duration": 300,
        "view_duration_std": 90,
        "categories_explored": (2, 3),
        "views_per_purchase": (5, 10),
        "price_preference": "high",
        "purchase_frequency": "low",
    },
    "TREND_FOLLOWER": {
        "avg_view_duration": 20,
        "view_duration_std": 10,
        "categories_explored": (3, 5),
        "views_per_purchase": (4, 7),
        "price_preference": "moderate",
        "purchase_frequency": "moderate",
    },
    "PRACTICAL_SHOPPER": {
        "avg_view_duration": 90,
        "view_duration_std": 30,
        "categories_explored": (1, 2),
        "views_per_purchase": (5, 8),
        "price_preference": "moderate",
        "purchase_frequency": "low",
    },
    "IMPULSE_BUYER": {
        "avg_view_duration": 10,
        "view_duration_std": 5,
        "categories_explored": (3, 5),
        "views_per_purchase": (1, 3),
        "price_preference": "moderate",
        "purchase_frequency": "very_high",
    },
}

def _normalize_hash_for_laravel(hash_bytes: bytes) -> str:
    """Convert $2b$ prefix (Python bcrypt) to $2y$ (PHP/Laravel bcrypt)."""
    return hash_bytes.decode("utf-8").replace("$2b$", "$2y$", 1)


ADMIN_PASSWORD_HASH = _normalize_hash_for_laravel(bcrypt.hashpw(b"password", bcrypt.gensalt()))
USER_PASSWORD_HASH = _normalize_hash_for_laravel(bcrypt.hashpw(b"password", bcrypt.gensalt()))

fake = Faker()
Faker.seed(0)

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args():
    p = argparse.ArgumentParser(
        description="Seed PostgreSQL with Amazon Reviews 2023 data"
    )
    p.add_argument(
        "--categories",
        nargs="+",
        default=CATEGORIES,
        help="Amazon categories to download",
    )
    p.add_argument(
        "--max-products",
        type=int,
        default=1000,
        help="Max products total (split across categories)",
    )
    p.add_argument("--max-users", type=int, default=300, help="Max unique users")
    p.add_argument("--max-reviews", type=int, default=5000, help="Max reviews")
    p.add_argument("--seed", type=int, default=42, help="Random seed")
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Download and transform only, don't insert",
    )
    p.add_argument(
        "--placeholder-images",
        action="store_true",
        help="Use placeholder image URLs instead of Amazon CDN",
    )
    return p.parse_args()


# ---------------------------------------------------------------------------
# Data Download (Streaming)
# ---------------------------------------------------------------------------


def download_amazon_data(categories, max_products, max_users, max_reviews):
    """Stream Amazon dataset from HuggingFace, collecting products and reviews."""
    from datasets import load_dataset

    products_per_cat = max_products // len(categories)
    reviews_per_cat = max_reviews // len(categories)

    all_products = {}  # asin -> product dict
    all_reviews = []
    all_user_ids = set()
    asin_to_category = {}

    for cat in categories:
        print(f"\n{'='*60}")
        print(f"Downloading: {cat}")
        print(f"{'='*60}")

        # --- Stream product metadata ---
        collected_asins = set()
        meta_name = f"raw_meta_{cat}"
        print(f"  Streaming {meta_name} for up to {products_per_cat} products...")

        try:
            meta_ds = load_dataset(
                "McAuley-Lab/Amazon-Reviews-2023",
                meta_name,
                split="full",
                streaming=True,
                trust_remote_code=True,
            )
        except Exception as e:
            print(f"  WARNING: Could not load {meta_name}: {e}")
            continue

        skipped = 0
        for item in meta_ds:
            if len(collected_asins) >= products_per_cat:
                break

            # Filter: must have title, price, and at least one image
            title = (item.get("title") or "").strip()
            if not title or title.lower() == "none":
                skipped += 1
                continue

            price = _parse_price(item.get("price"))
            if price is None:
                # Assign a random price for the category
                lo, hi = CATEGORY_PRICE_RANGES.get(cat, (10.0, 100.0))
                price = round(random.uniform(lo, hi), 2)

            images = item.get("images", {})
            image_urls = []
            if isinstance(images, dict):
                for key in ("large", "hi_res", "thumb"):
                    urls = images.get(key, [])
                    if urls:
                        image_urls = [u for u in urls if u and u != "None"]
                        if image_urls:
                            break
            elif isinstance(images, list):
                image_urls = [u for u in images if u and u != "None"]

            asin = item.get("parent_asin") or item.get("asin") or ""
            if not asin or asin in collected_asins:
                skipped += 1
                continue

            # Description
            desc = item.get("description", [])
            if isinstance(desc, list):
                desc = " ".join(str(d) for d in desc if d)
            desc = (desc or "").strip()
            if not desc:
                # Use features as fallback
                features = item.get("features", [])
                if isinstance(features, list):
                    desc = " ".join(str(f) for f in features if f)

            # Sub-category
            cats = item.get("categories", [])
            store = item.get("store") or ""
            sub_cat = None
            if isinstance(cats, list) and len(cats) > 1:
                sub_cat = str(cats[1]).strip()
            elif store:
                sub_cat = store.strip()

            collected_asins.add(asin)
            asin_to_category[asin] = cat

            all_products[asin] = {
                "asin": asin,
                "title": title[:255],
                "description": desc[:5000] if desc else f"Product from {cat}",
                "price": price,
                "image_urls": image_urls[:5],  # keep up to 5
                "main_category": cat,
                "sub_category": sub_cat,
                "average_rating": item.get("average_rating"),
                "rating_number": item.get("rating_number"),
            }

        print(
            f"  Collected {len(collected_asins)} products (skipped {skipped})"
        )

        # --- Stream reviews for collected ASINs ---
        review_name = f"raw_review_{cat}"
        print(f"  Streaming {review_name} for reviews...")

        try:
            review_ds = load_dataset(
                "McAuley-Lab/Amazon-Reviews-2023",
                review_name,
                split="full",
                streaming=True,
                trust_remote_code=True,
            )
        except Exception as e:
            print(f"  WARNING: Could not load {review_name}: {e}")
            continue

        cat_reviews = 0
        scanned = 0
        max_scan = max(reviews_per_cat * 2000, 50000)  # Don't scan forever
        for item in review_ds:
            scanned += 1
            if scanned % 10000 == 0:
                print(f"    ... scanned {scanned} reviews, matched {cat_reviews} so far")
            if cat_reviews >= reviews_per_cat:
                break
            if scanned >= max_scan:
                print(f"    ... reached scan limit ({max_scan}), moving on")
                break
            if len(all_user_ids) >= max_users and item.get("user_id") not in all_user_ids:
                continue

            asin = item.get("parent_asin") or item.get("asin") or ""
            if asin not in collected_asins:
                continue

            text = (item.get("text") or "").strip()
            if not text:
                continue

            rating = item.get("rating")
            if rating is None:
                continue
            try:
                rating = int(float(rating))
                if rating < 1 or rating > 5:
                    continue
            except (ValueError, TypeError):
                continue

            user_id = item.get("user_id") or ""
            if not user_id:
                continue

            timestamp = item.get("timestamp")
            verified = item.get("verified_purchase", False)

            all_user_ids.add(user_id)
            all_reviews.append(
                {
                    "asin": asin,
                    "amazon_user_id": user_id,
                    "rating": rating,
                    "text": text[:5000],
                    "timestamp": timestamp,
                    "verified_purchase": verified,
                    "category": cat,
                }
            )
            cat_reviews += 1

        print(f"  Collected {cat_reviews} reviews, {len(all_user_ids)} unique users so far")

    print(f"\n{'='*60}")
    print(f"Download complete:")
    print(f"  Products: {len(all_products)}")
    print(f"  Reviews:  {len(all_reviews)}")
    print(f"  Users:    {len(all_user_ids)}")
    print(f"{'='*60}")

    return all_products, all_reviews, all_user_ids


def _parse_price(val):
    """Try to parse a price value from Amazon data."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return round(float(val), 2) if val > 0 else None
    s = str(val).strip().replace("$", "").replace(",", "")
    if not s or s.lower() == "none":
        return None
    # Handle ranges like "19.99 - 29.99" -> take lower
    if " - " in s:
        s = s.split(" - ")[0].strip()
    try:
        p = float(s)
        return round(p, 2) if p > 0 else None
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Data Transformation
# ---------------------------------------------------------------------------


def transform_data(
    raw_products, raw_reviews, raw_user_ids, args
):
    """Map Amazon data to our DB schema and generate synthetic data."""
    rng = random.Random(args.seed)
    fake_local = Faker()
    Faker.seed(args.seed)

    now = datetime.now(timezone.utc)

    # --- Build ID mappings ---
    asin_list = list(raw_products.keys())
    rng.shuffle(asin_list)
    asin_to_id = {asin: idx + 1 for idx, asin in enumerate(asin_list)}

    user_id_list = list(raw_user_ids)
    rng.shuffle(user_id_list)
    # User IDs start at 2 (1 = admin)
    amazon_user_to_id = {uid: idx + 2 for idx, uid in enumerate(user_id_list)}

    # --- Categories ---
    categories = []
    cat_id = 0
    main_cat_ids = {}
    sub_cat_map = {}  # (main_cat, sub_cat_name) -> cat_id

    for main_cat in sorted(set(p["main_category"] for p in raw_products.values())):
        cat_id += 1
        display_name = main_cat.replace("_", " & " if "_and_" in main_cat else " ")
        display_name = main_cat.replace("_and_", " & ").replace("_", " ")
        categories.append(
            {
                "id": cat_id,
                "name": display_name,
                "parent_id": None,
                "created_at": now,
                "updated_at": now,
            }
        )
        main_cat_ids[main_cat] = cat_id

        # Collect sub-categories from products
        product_sub_cats = set()
        for p in raw_products.values():
            if p["main_category"] == main_cat and p["sub_category"]:
                product_sub_cats.add(p["sub_category"])

        # Use product sub-cats if available, else defaults
        subs = list(product_sub_cats)[:8] if product_sub_cats else DEFAULT_SUBCATEGORIES.get(main_cat, [])
        for sub_name in subs:
            cat_id += 1
            categories.append(
                {
                    "id": cat_id,
                    "name": sub_name[:255],
                    "parent_id": main_cat_ids[main_cat],
                    "created_at": now,
                    "updated_at": now,
                }
            )
            sub_cat_map[(main_cat, sub_name)] = cat_id

    # --- Products ---
    products = []
    product_images = []
    img_id = 0

    for asin, p in raw_products.items():
        pid = asin_to_id[asin]
        main_cat = p["main_category"]

        # Pick best sub-category id
        if p["sub_category"] and (main_cat, p["sub_category"]) in sub_cat_map:
            cat_id_for_product = sub_cat_map[(main_cat, p["sub_category"])]
        else:
            # Assign to a random sub-category of this main category
            possible = [
                cid
                for (mc, _), cid in sub_cat_map.items()
                if mc == main_cat
            ]
            cat_id_for_product = rng.choice(possible) if possible else main_cat_ids[main_cat]

        image_url = None
        if not args.placeholder_images and p["image_urls"]:
            image_url = p["image_urls"][0]
        elif args.placeholder_images:
            image_url = f"https://placehold.co/400x400?text={pid}"

        products.append(
            {
                "id": pid,
                "name": p["title"],
                "description": p["description"],
                "price": p["price"],
                "stock": rng.randint(0, 500),
                "low_stock_threshold": 10,
                "track_stock": True,
                "category_id": cat_id_for_product,
                "image_url": image_url,
                "created_at": now,
            }
        )

        # Product images
        urls = p["image_urls"] if not args.placeholder_images else []
        if args.placeholder_images:
            urls = [f"https://placehold.co/400x400?text={pid}-{i}" for i in range(rng.randint(1, 3))]
        for i, url in enumerate(urls):
            img_id += 1
            product_images.append(
                {
                    "id": img_id,
                    "product_id": pid,
                    "url": url,
                    "alt_text": p["title"][:255],
                    "is_primary": i == 0,
                    "sort_order": i,
                    "created_at": now,
                }
            )

    # Map products to categories for interaction generation
    product_category_map = {p["id"]: p["category_id"] for p in products}
    product_price_map = {p["id"]: p["price"] for p in products}
    # Map category_id -> main_category name
    cat_id_to_main = {}
    for main_cat, mcid in main_cat_ids.items():
        cat_id_to_main[mcid] = main_cat
        for (mc, _), scid in sub_cat_map.items():
            if mc == main_cat:
                cat_id_to_main[scid] = main_cat

    # --- Users ---
    users = []
    for amazon_uid, uid in amazon_user_to_id.items():
        first = fake_local.first_name()
        last = fake_local.last_name()
        users.append(
            {
                "id": uid,
                "name": f"{first} {last}",
                "email": f"user_{uid}@example.com",
                "email_verified_at": now - timedelta(days=rng.randint(1, 90)),
                "password": USER_PASSWORD_HASH,
                "remember_token": None,
                "created_at": now - timedelta(days=rng.randint(30, 365)),
                "updated_at": now,
                "is_admin": False,
                "phone": fake_local.phone_number()[:20] if rng.random() > 0.5 else None,
                "avatar_url": None,
                "date_of_birth": fake_local.date_of_birth(
                    minimum_age=18, maximum_age=70
                )
                if rng.random() > 0.6
                else None,
                "preferences": None,
            }
        )

    # --- Reviews ---
    reviews = []
    review_id = 0
    user_purchases = defaultdict(set)  # user_id -> set of product_ids (verified)

    for r in raw_reviews:
        uid = amazon_user_to_id.get(r["amazon_user_id"])
        pid = asin_to_id.get(r["asin"])
        if uid is None or pid is None:
            continue

        review_id += 1

        # Parse timestamp
        ts = r["timestamp"]
        if isinstance(ts, (int, float)):
            # Unix ms
            created = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
        elif isinstance(ts, datetime):
            created = ts.replace(tzinfo=timezone.utc) if ts.tzinfo is None else ts
        else:
            created = now - timedelta(days=rng.randint(1, 365))

        reviews.append(
            {
                "id": review_id,
                "user_id": uid,
                "product_id": pid,
                "rating": r["rating"],
                "comment": r["text"],
                "sentiment_score": None,
                "sentiment_label": None,
                "sentiment_confidence": None,
                "sentiment_analyzed_at": None,
                "created_at": created,
            }
        )

        if r.get("verified_purchase"):
            user_purchases[uid].add(pid)

    # --- Addresses ---
    addresses = []
    addr_id = 0
    user_address_map = {}  # user_id -> (shipping_id, billing_id)

    for u in users:
        uid = u["id"]
        # Shipping address (everyone gets one)
        addr_id += 1
        shipping_id = addr_id
        addresses.append(_make_address(addr_id, uid, "shipping", True, fake_local, now))

        billing_id = None
        if rng.random() > 0.5:
            addr_id += 1
            billing_id = addr_id
            addresses.append(
                _make_address(addr_id, uid, "billing", False, fake_local, now)
            )

        user_address_map[uid] = (shipping_id, billing_id)

    # --- Orders (derived from verified purchases) ---
    orders = []
    order_items = []
    order_id = 0
    order_item_id = 0

    # Group verified purchases by user, then create orders
    for uid, purchased_pids in user_purchases.items():
        if not purchased_pids:
            continue

        # Group into orders (1-5 items per order)
        pid_list = list(purchased_pids)
        rng.shuffle(pid_list)

        i = 0
        while i < len(pid_list):
            batch_size = min(rng.randint(1, 5), len(pid_list) - i)
            batch = pid_list[i : i + batch_size]
            i += batch_size

            order_id += 1
            ship_id, bill_id = user_address_map.get(uid, (None, None))

            # Timestamps
            base_review = None
            for rv in reviews:
                if rv["user_id"] == uid and rv["product_id"] in batch:
                    base_review = rv["created_at"]
                    break
            if base_review is None:
                base_review = now - timedelta(days=rng.randint(7, 60))

            ordered_at = base_review - timedelta(days=rng.randint(7, 30))
            confirmed_at = ordered_at + timedelta(hours=rng.randint(1, 12))
            shipped_at = confirmed_at + timedelta(days=rng.randint(1, 3))
            delivered_at = shipped_at + timedelta(days=rng.randint(2, 7))

            subtotal = 0.0
            items_for_order = []
            for pid in batch:
                order_item_id += 1
                price = product_price_map.get(pid, 29.99)
                qty = rng.choices([1, 2, 3], weights=[0.7, 0.2, 0.1])[0]
                item_subtotal = round(price * qty, 2)
                subtotal += item_subtotal

                # Find product name
                pname = ""
                for pr in products:
                    if pr["id"] == pid:
                        pname = pr["name"]
                        break

                items_for_order.append(
                    {
                        "id": order_item_id,
                        "order_id": order_id,
                        "product_id": pid,
                        "product_name": pname[:255],
                        "product_price": price,
                        "quantity": qty,
                        "subtotal": item_subtotal,
                    }
                )

            tax = round(subtotal * 0.08, 2)
            total = round(subtotal + tax, 2)

            orders.append(
                {
                    "id": order_id,
                    "order_number": f"ORD-{order_id:06d}",
                    "user_id": uid,
                    "shipping_address_id": ship_id,
                    "billing_address_id": bill_id,
                    "status": "delivered",
                    "subtotal": round(subtotal, 2),
                    "discount": 0.00,
                    "tax": tax,
                    "total": total,
                    "notes": None,
                    "ordered_at": ordered_at,
                    "confirmed_at": confirmed_at,
                    "shipped_at": shipped_at,
                    "delivered_at": delivered_at,
                    "cancelled_at": None,
                }
            )
            order_items.extend(items_for_order)

    # Build product name lookup for fast access
    product_name_map = {p["id"]: p["name"] for p in products}

    # --- Wishlists ---
    wishlists = []
    wl_id = 0
    all_pids = [p["id"] for p in products]

    for u in users:
        uid = u["id"]
        purchased = user_purchases.get(uid, set())
        available = [pid for pid in all_pids if pid not in purchased]
        if not available:
            continue
        count = rng.randint(2, 5)
        picks = rng.sample(available, min(count, len(available)))
        for pid in picks:
            wl_id += 1
            wishlists.append(
                {
                    "id": wl_id,
                    "user_id": uid,
                    "product_id": pid,
                    "added_at": now - timedelta(days=rng.randint(1, 30)),
                }
            )

    # --- Carts (30% of users) ---
    carts = []
    cart_items_list = []
    cart_id = 0
    cart_item_id = 0

    cart_users = rng.sample(
        [u["id"] for u in users], k=max(1, int(len(users) * 0.3))
    )
    for uid in cart_users:
        cart_id += 1
        carts.append(
            {
                "id": cart_id,
                "user_id": uid,
                "created_at": now - timedelta(days=rng.randint(0, 7)),
                "updated_at": now,
            }
        )
        num_items = rng.randint(1, 3)
        picked = rng.sample(all_pids, min(num_items, len(all_pids)))
        for pid in picked:
            cart_item_id += 1
            cart_items_list.append(
                {
                    "id": cart_item_id,
                    "cart_id": cart_id,
                    "product_id": pid,
                    "quantity": rng.choices([1, 2, 3], weights=[0.7, 0.2, 0.1])[0],
                    "added_at": now - timedelta(days=rng.randint(0, 5)),
                }
            )

    # --- User Interactions (archetype-driven) ---
    interactions = _generate_interactions(
        users,
        products,
        user_purchases,
        product_category_map,
        product_price_map,
        cat_id_to_main,
        orders,
        order_items,
        rng,
        now,
    )

    return {
        "categories": categories,
        "products": products,
        "product_images": product_images,
        "users": users,
        "addresses": addresses,
        "reviews": reviews,
        "orders": orders,
        "order_items": order_items,
        "wishlists": wishlists,
        "carts": carts,
        "cart_items": cart_items_list,
        "interactions": interactions,
    }


def _make_address(addr_id, user_id, addr_type, is_default, fake_local, now):
    return {
        "id": addr_id,
        "user_id": user_id,
        "label": f"My {addr_type.title()} Address",
        "type": addr_type,
        "first_name": fake_local.first_name(),
        "last_name": fake_local.last_name(),
        "phone": fake_local.phone_number()[:20],
        "address_line_1": fake_local.street_address(),
        "address_line_2": fake_local.secondary_address() if random.random() > 0.6 else None,
        "city": fake_local.city(),
        "state": fake_local.state_abbr(),
        "postal_code": fake_local.zipcode(),
        "country": "US",
        "is_default": is_default,
        "created_at": now,
    }


def _generate_interactions(
    users,
    products,
    user_purchases,
    product_category_map,
    product_price_map,
    cat_id_to_main,
    orders,
    order_items,
    rng,
    now,
):
    """Generate personality-archetype-driven user interactions."""
    archetype_names = list(PERSONALITY_ARCHETYPES.keys())
    interactions = []

    # Group products by main category
    products_by_main_cat = defaultdict(list)
    for p in products:
        cid = p["category_id"]
        main = cat_id_to_main.get(cid, "Other")
        products_by_main_cat[main].append(p["id"])

    all_main_cats = list(products_by_main_cat.keys())
    all_pids = [p["id"] for p in products]

    # Build order lookup: user_id -> list of (order, items)
    order_lookup = defaultdict(list)
    for o in orders:
        items = [oi for oi in order_items if oi["order_id"] == o["id"]]
        order_lookup[o["user_id"]].append((o, items))

    for i, u in enumerate(users):
        uid = u["id"]
        archetype_name = archetype_names[i % len(archetype_names)]
        arch = PERSONALITY_ARCHETYPES[archetype_name]

        purchased_pids = user_purchases.get(uid, set())
        user_orders = order_lookup.get(uid, [])

        # Determine categories this user explores
        n_cats = rng.randint(*arch["categories_explored"])
        # Prefer categories where user purchased
        user_cat_pids = defaultdict(list)
        for pid in purchased_pids:
            cid = product_category_map.get(pid)
            main = cat_id_to_main.get(cid, "Other") if cid else "Other"
            user_cat_pids[main].append(pid)

        preferred_cats = list(user_cat_pids.keys())
        other_cats = [c for c in all_main_cats if c not in preferred_cats]
        rng.shuffle(other_cats)
        explored_cats = (preferred_cats + other_cats)[:n_cats]

        # --- Purchase interactions ---
        for order, items in user_orders:
            for oi in items:
                pid = oi["product_id"]
                delivered = order.get("delivered_at") or now - timedelta(days=5)

                # purchase event
                interactions.append(
                    _make_interaction(
                        uid,
                        pid,
                        "purchase",
                        0,
                        {"order_id": order["id"], "archetype": archetype_name},
                        delivered,
                    )
                )

                # add_to_cart before purchase
                cart_time = delivered - timedelta(
                    days=rng.randint(1, 3), hours=rng.randint(0, 12)
                )
                interactions.append(
                    _make_interaction(
                        uid,
                        pid,
                        "add_to_cart",
                        0,
                        {"archetype": archetype_name},
                        cart_time,
                    )
                )

                # Views before purchase
                n_views = rng.randint(*arch["views_per_purchase"])
                for v in range(n_views):
                    view_time = cart_time - timedelta(
                        days=rng.randint(0, 5), hours=rng.randint(0, 23)
                    )
                    dur = max(
                        1,
                        int(
                            rng.gauss(
                                arch["avg_view_duration"],
                                arch["view_duration_std"],
                            )
                        ),
                    )
                    interactions.append(
                        _make_interaction(
                            uid,
                            pid,
                            "view",
                            dur,
                            {"archetype": archetype_name},
                            view_time,
                        )
                    )

                    # click for 50-70% of views
                    if rng.random() < rng.uniform(0.5, 0.7):
                        click_time = view_time + timedelta(seconds=rng.randint(2, max(dur, 3)))
                        interactions.append(
                            _make_interaction(
                                uid,
                                pid,
                                "click",
                                0,
                                {"archetype": archetype_name},
                                click_time,
                            )
                        )

        # --- Browsing interactions (non-purchased products) ---
        n_browse = rng.randint(10, 40)
        browse_pool = []
        for cat in explored_cats:
            browse_pool.extend(products_by_main_cat.get(cat, []))
        browse_pool = [pid for pid in browse_pool if pid not in purchased_pids]
        if not browse_pool:
            browse_pool = [pid for pid in all_pids if pid not in purchased_pids]

        if browse_pool:
            browse_pids = [rng.choice(browse_pool) for _ in range(n_browse)]
            for pid in browse_pids:
                view_time = now - timedelta(
                    days=rng.randint(0, 29),
                    hours=rng.randint(0, 23),
                    minutes=rng.randint(0, 59),
                )
                dur = max(
                    1,
                    int(
                        rng.gauss(
                            arch["avg_view_duration"], arch["view_duration_std"]
                        )
                    ),
                )
                interactions.append(
                    _make_interaction(
                        uid,
                        pid,
                        "view",
                        dur,
                        {"archetype": archetype_name},
                        view_time,
                    )
                )

                if rng.random() < 0.4:
                    click_time = view_time + timedelta(seconds=rng.randint(2, max(3, dur)))
                    interactions.append(
                        _make_interaction(
                            uid,
                            pid,
                            "click",
                            0,
                            {"archetype": archetype_name},
                            click_time,
                        )
                    )

    # Ensure all interactions are within last 30 days
    cutoff = now - timedelta(days=30)
    for ix in interactions:
        if ix["created_at"] < cutoff:
            # Shift to within the window
            ix["created_at"] = cutoff + timedelta(
                seconds=rng.randint(0, 30 * 24 * 3600)
            )

    return interactions


def _make_interaction(user_id, product_id, itype, duration, metadata, created_at):
    return {
        "id": uuid4(),
        "user_id": user_id,
        "product_id": product_id,
        "interaction_type": itype,
        "duration_seconds": duration,
        "metadata": json.dumps(metadata) if metadata else None,
        "created_at": created_at,
    }


# ---------------------------------------------------------------------------
# Clear ML Databases (MongoDB, Weaviate, Redis)
# ---------------------------------------------------------------------------


async def clear_ml_databases():
    """Drop stale ML data from MongoDB, Weaviate, and Redis."""

    # --- MongoDB ---
    print("Clearing MongoDB (ml_service)...")
    try:
        from motor.motor_asyncio import AsyncIOMotorClient

        mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        mongo_db = os.getenv("MONGO_DB", "ml_service")
        client = AsyncIOMotorClient(mongo_uri)
        db = client[mongo_db]
        for collection in ("user_profiles", "sentiment_history", "ml_features"):
            result = await db[collection].delete_many({})
            print(f"  {collection}: deleted {result.deleted_count} documents")
        client.close()
    except Exception as e:
        print(f"  WARNING: Could not clear MongoDB: {e}")

    # --- Weaviate ---
    print("Clearing Weaviate collections...")
    try:
        import weaviate

        weaviate_url = os.getenv("WEAVIATE_URL", "http://localhost:8085")
        wv_client = weaviate.connect_to_local(
            host=weaviate_url.replace("http://", "").split(":")[0],
            port=int(weaviate_url.split(":")[-1]),
            grpc_port=int(os.getenv("WEAVIATE_GRPC_PORT", "50051")),
        )
        for class_name in ("Product", "UserPreference"):
            try:
                wv_client.collections.delete(class_name)
                print(f"  {class_name}: deleted")
            except Exception:
                print(f"  {class_name}: not found (skipping)")
        wv_client.close()
    except Exception as e:
        print(f"  WARNING: Could not clear Weaviate: {e}")

    # --- Redis ---
    print("Clearing Redis cache...")
    try:
        import redis as redis_lib

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        r = redis_lib.from_url(redis_url)
        flushed = r.flushdb()
        print(f"  Redis DB flushed: {flushed}")
        r.close()
    except Exception as e:
        print(f"  WARNING: Could not clear Redis: {e}")


# ---------------------------------------------------------------------------
# Database Insertion
# ---------------------------------------------------------------------------


def _strip_tz(dt):
    """Convert timezone-aware datetime to naive UTC for PostgreSQL timestamp columns."""
    if dt is not None and hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt


def _strip_tz_in_records(records):
    """Strip timezone from all datetime values in a list of dicts."""
    for rec in records:
        for k, v in rec.items():
            if isinstance(v, datetime):
                rec[k] = _strip_tz(v)
    return records


async def insert_data(data, args):
    """Insert transformed data into PostgreSQL and clear ML databases."""
    dsn = (
        f"postgresql://{os.getenv('POSTGRES_USER', 'postgres')}"
        f":{os.getenv('POSTGRES_PASSWORD', 'secret')}"
        f"@{os.getenv('POSTGRES_HOST', 'localhost')}"
        f":{os.getenv('POSTGRES_PORT', '5432')}"
        f"/{os.getenv('POSTGRES_DB', 'backend')}"
    )

    print(f"\nConnecting to PostgreSQL...")
    conn = await asyncpg.connect(dsn)

    try:
        # Truncate all tables (order matters for FKs)
        print("Truncating tables...")
        await conn.execute("""
            TRUNCATE TABLE
                user_interactions,
                cart_items, carts,
                wishlists,
                order_items, orders,
                reviews,
                addresses,
                product_images,
                products,
                categories,
                personal_access_tokens,
                sessions,
                users
            CASCADE
        """)

        # Clear ML databases (MongoDB, Weaviate, Redis)
        await clear_ml_databases()

        # Strip timezone info from all datetime values for PostgreSQL timestamp columns
        for key in data:
            if isinstance(data[key], list):
                _strip_tz_in_records(data[key])

        # Re-insert admin user
        print("Inserting admin user...")
        await conn.execute(
            """
            INSERT INTO users (id, name, email, email_verified_at, password,
                               created_at, updated_at, is_admin)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            1,
            "Admin User",
            "admin@admin.com",
            _strip_tz(datetime.now(timezone.utc)),
            ADMIN_PASSWORD_HASH,
            _strip_tz(datetime.now(timezone.utc)),
            _strip_tz(datetime.now(timezone.utc)),
            True,
        )

        # --- Categories ---
        print(f"Inserting {len(data['categories'])} categories...")
        await conn.executemany(
            """
            INSERT INTO categories (id, name, parent_id, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5)
            """,
            [
                (c["id"], c["name"], c["parent_id"], c["created_at"], c["updated_at"])
                for c in data["categories"]
            ],
        )

        # --- Products ---
        print(f"Inserting {len(data['products'])} products...")
        await conn.executemany(
            """
            INSERT INTO products (id, name, description, price, stock,
                                  low_stock_threshold, track_stock,
                                  category_id, image_url, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
            [
                (
                    p["id"], p["name"], p["description"], p["price"],
                    p["stock"], p["low_stock_threshold"], p["track_stock"],
                    p["category_id"], p["image_url"], p["created_at"],
                )
                for p in data["products"]
            ],
        )

        # --- Product Images ---
        print(f"Inserting {len(data['product_images'])} product images...")
        if data["product_images"]:
            await conn.executemany(
                """
                INSERT INTO product_images (id, product_id, url, alt_text,
                                            is_primary, sort_order, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                [
                    (
                        pi["id"], pi["product_id"], pi["url"], pi["alt_text"],
                        pi["is_primary"], pi["sort_order"], pi["created_at"],
                    )
                    for pi in data["product_images"]
                ],
            )

        # --- Users ---
        print(f"Inserting {len(data['users'])} users...")
        await conn.executemany(
            """
            INSERT INTO users (id, name, email, email_verified_at, password,
                               remember_token, created_at, updated_at, is_admin,
                               phone, avatar_url, date_of_birth, preferences)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            """,
            [
                (
                    u["id"], u["name"], u["email"], u["email_verified_at"],
                    u["password"], u["remember_token"], u["created_at"],
                    u["updated_at"], u["is_admin"], u["phone"],
                    u["avatar_url"], u["date_of_birth"], u["preferences"],
                )
                for u in data["users"]
            ],
        )

        # --- Addresses ---
        print(f"Inserting {len(data['addresses'])} addresses...")
        await conn.executemany(
            """
            INSERT INTO addresses (id, user_id, label, type, first_name, last_name,
                                   phone, address_line_1, address_line_2, city,
                                   state, postal_code, country, is_default, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
            """,
            [
                (
                    a["id"], a["user_id"], a["label"], a["type"],
                    a["first_name"], a["last_name"], a["phone"],
                    a["address_line_1"], a["address_line_2"], a["city"],
                    a["state"], a["postal_code"], a["country"],
                    a["is_default"], a["created_at"],
                )
                for a in data["addresses"]
            ],
        )

        # --- Reviews ---
        print(f"Inserting {len(data['reviews'])} reviews...")
        await conn.executemany(
            """
            INSERT INTO reviews (id, user_id, product_id, rating, comment,
                                 sentiment_score, sentiment_label,
                                 sentiment_confidence, sentiment_analyzed_at,
                                 created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
            [
                (
                    r["id"], r["user_id"], r["product_id"], r["rating"],
                    r["comment"], r["sentiment_score"], r["sentiment_label"],
                    r["sentiment_confidence"], r["sentiment_analyzed_at"],
                    r["created_at"],
                )
                for r in data["reviews"]
            ],
        )

        # --- Orders ---
        print(f"Inserting {len(data['orders'])} orders...")
        await conn.executemany(
            """
            INSERT INTO orders (id, order_number, user_id, shipping_address_id,
                                billing_address_id, status, subtotal, discount,
                                tax, total, notes, ordered_at, confirmed_at,
                                shipped_at, delivered_at, cancelled_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
            """,
            [
                (
                    o["id"], o["order_number"], o["user_id"],
                    o["shipping_address_id"], o["billing_address_id"],
                    o["status"], o["subtotal"], o["discount"], o["tax"],
                    o["total"], o["notes"], o["ordered_at"],
                    o["confirmed_at"], o["shipped_at"], o["delivered_at"],
                    o["cancelled_at"],
                )
                for o in data["orders"]
            ],
        )

        # --- Order Items ---
        print(f"Inserting {len(data['order_items'])} order items...")
        if data["order_items"]:
            await conn.executemany(
                """
                INSERT INTO order_items (id, order_id, product_id, product_name,
                                         product_price, quantity, subtotal)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                [
                    (
                        oi["id"], oi["order_id"], oi["product_id"],
                        oi["product_name"], oi["product_price"],
                        oi["quantity"], oi["subtotal"],
                    )
                    for oi in data["order_items"]
                ],
            )

        # --- Wishlists ---
        print(f"Inserting {len(data['wishlists'])} wishlist items...")
        if data["wishlists"]:
            await conn.executemany(
                """
                INSERT INTO wishlists (id, user_id, product_id, added_at)
                VALUES ($1, $2, $3, $4)
                """,
                [
                    (w["id"], w["user_id"], w["product_id"], w["added_at"])
                    for w in data["wishlists"]
                ],
            )

        # --- Carts ---
        print(f"Inserting {len(data['carts'])} carts...")
        if data["carts"]:
            await conn.executemany(
                """
                INSERT INTO carts (id, user_id, created_at, updated_at)
                VALUES ($1, $2, $3, $4)
                """,
                [
                    (c["id"], c["user_id"], c["created_at"], c["updated_at"])
                    for c in data["carts"]
                ],
            )

        # --- Cart Items ---
        print(f"Inserting {len(data['cart_items'])} cart items...")
        if data["cart_items"]:
            await conn.executemany(
                """
                INSERT INTO cart_items (id, cart_id, product_id, quantity, added_at)
                VALUES ($1, $2, $3, $4, $5)
                """,
                [
                    (
                        ci["id"], ci["cart_id"], ci["product_id"],
                        ci["quantity"], ci["added_at"],
                    )
                    for ci in data["cart_items"]
                ],
            )

        # --- User Interactions ---
        print(f"Inserting {len(data['interactions'])} user interactions...")
        if data["interactions"]:
            # Use copy for bulk insert (much faster for large datasets)
            await conn.copy_records_to_table(
                "user_interactions",
                records=[
                    (
                        ix["id"],
                        ix["user_id"],
                        ix["product_id"],
                        ix["interaction_type"],
                        ix["duration_seconds"],
                        ix["metadata"],
                        ix["created_at"],
                    )
                    for ix in data["interactions"]
                ],
                columns=[
                    "id", "user_id", "product_id", "interaction_type",
                    "duration_seconds", "metadata", "created_at",
                ],
            )

        # --- Reset sequences ---
        print("Resetting sequences...")
        sequences = [
            ("users", "id"),
            ("categories", "id"),
            ("products", "id"),
            ("product_images", "id"),
            ("addresses", "id"),
            ("reviews", "id"),
            ("orders", "id"),
            ("order_items", "id"),
            ("wishlists", "id"),
            ("carts", "id"),
            ("cart_items", "id"),
        ]
        for table, col in sequences:
            await conn.execute(
                f"SELECT setval(pg_get_serial_sequence('{table}', '{col}'), "
                f"COALESCE((SELECT MAX({col}) FROM {table}), 0) + 1, false)"
            )

        print("\nDatabase seeded successfully!")

    finally:
        await conn.close()


# ---------------------------------------------------------------------------
# Summary & Verification
# ---------------------------------------------------------------------------


async def print_summary(args):
    """Print row counts and ML readiness checks."""
    dsn = (
        f"postgresql://{os.getenv('POSTGRES_USER', 'postgres')}"
        f":{os.getenv('POSTGRES_PASSWORD', 'secret')}"
        f"@{os.getenv('POSTGRES_HOST', 'localhost')}"
        f":{os.getenv('POSTGRES_PORT', '5432')}"
        f"/{os.getenv('POSTGRES_DB', 'backend')}"
    )

    conn = await asyncpg.connect(dsn)
    try:
        tables = [
            "users", "categories", "products", "product_images",
            "addresses", "reviews", "orders", "order_items",
            "wishlists", "carts", "cart_items", "user_interactions",
        ]

        print(f"\n{'='*50}")
        print("DATABASE SUMMARY")
        print(f"{'='*50}")
        print(f"{'Table':<25} {'Count':>10}")
        print(f"{'-'*35}")

        for table in tables:
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
            print(f"{table:<25} {count:>10,}")

        # ML readiness check
        print(f"\n{'='*50}")
        print("ML READINESS CHECKS")
        print(f"{'='*50}")

        # Users with sufficient data points
        result = await conn.fetchval("""
            WITH user_data_points AS (
                SELECT
                    u.id,
                    (SELECT COUNT(*) FROM reviews r WHERE r.user_id = u.id) +
                    (SELECT COUNT(*) FROM order_items oi
                     JOIN orders o ON o.id = oi.order_id
                     WHERE o.user_id = u.id) +
                    (SELECT COUNT(*) FROM user_interactions ui WHERE ui.user_id = u.id)
                    AS total_points
                FROM users u
                WHERE u.id > 1
            )
            SELECT ROUND(
                100.0 * COUNT(*) FILTER (WHERE total_points >= 5)
                / NULLIF(COUNT(*), 0), 1
            )
            FROM user_data_points
        """)
        print(f"Users with >= 5 data points: {result}%")

        # Interaction type distribution
        rows = await conn.fetch("""
            SELECT interaction_type, COUNT(*) as cnt
            FROM user_interactions
            GROUP BY interaction_type
            ORDER BY cnt DESC
        """)
        print("\nInteraction distribution:")
        for row in rows:
            print(f"  {row['interaction_type']:<15} {row['cnt']:>8,}")

        # Archetype distribution
        archetype_count = await conn.fetchval("""
            SELECT COUNT(DISTINCT metadata::jsonb->>'archetype')
            FROM user_interactions
            WHERE metadata IS NOT NULL
        """)
        print(f"\nPersonality archetypes present: {archetype_count}")

        # Category distribution
        rows = await conn.fetch("""
            SELECT c.name, COUNT(p.id) as product_count
            FROM categories c
            LEFT JOIN products p ON p.category_id = c.id
            WHERE c.parent_id IS NOT NULL
            GROUP BY c.name
            HAVING COUNT(p.id) > 0
            ORDER BY product_count DESC
            LIMIT 10
        """)
        print("\nTop categories by product count:")
        for row in rows:
            print(f"  {row['name']:<30} {row['product_count']:>5}")

        print(f"\n{'='*50}")
        print("Seeding complete! The database is ready for ML services.")
        print(f"{'='*50}")

    finally:
        await conn.close()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    args = parse_args()

    # Load .env from ml-services directory
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    load_dotenv(env_path)

    random.seed(args.seed)

    print("=" * 60)
    print("Amazon Reviews 2023 Database Seeder")
    print("=" * 60)
    print(f"Categories:    {', '.join(args.categories)}")
    print(f"Max products:  {args.max_products}")
    print(f"Max users:     {args.max_users}")
    print(f"Max reviews:   {args.max_reviews}")
    print(f"Random seed:   {args.seed}")
    print(f"Dry run:       {args.dry_run}")
    print(f"Placeholders:  {args.placeholder_images}")
    print()

    # Step 1: Download
    t0 = time.time()
    raw_products, raw_reviews, raw_user_ids = download_amazon_data(
        args.categories, args.max_products, args.max_users, args.max_reviews
    )
    t1 = time.time()
    print(f"\nDownload took {t1 - t0:.1f}s")

    if not raw_products:
        print("ERROR: No products downloaded. Check your internet connection.")
        sys.exit(1)

    # Step 2: Transform
    print("\nTransforming data...")
    data = transform_data(raw_products, raw_reviews, raw_user_ids, args)
    t2 = time.time()
    print(f"Transform took {t2 - t1:.1f}s")

    # Print preview
    print(f"\nData preview:")
    for key, val in data.items():
        print(f"  {key:<20} {len(val):>8,} records")

    if args.dry_run:
        print("\n[DRY RUN] Skipping database insertion.")
        return

    # Step 3: Insert
    print("\nInserting into database...")
    asyncio.run(insert_data(data, args))
    t3 = time.time()
    print(f"Insert took {t3 - t2:.1f}s")

    # Step 4: Verify
    asyncio.run(print_summary(args))

    total = time.time() - t0
    print(f"\nTotal time: {total:.1f}s")


if __name__ == "__main__":
    main()
