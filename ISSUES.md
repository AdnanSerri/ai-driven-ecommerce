# Issues Tracker

This file tracks bugs, issues, API problems, and questions to be fixed.

---

## Pending Issues

*No pending issues*

---

## Fixed Issues

### Issue #12: Personality Profile Not Rendering on Profile Page
**Fixed:** Data mapping between ML service and NestJS was incorrect
- ML service returns `{ profile: { dimensions, ... } }` but controller accessed wrong fields
- Fixed to properly extract `profile.dimensions` and map to `traits`
- Traits endpoint now transforms dimensions array to `{ name: score }` object
**Files Changed:**
- `nestjs-backend/src/ml/personality.controller.ts` - Fixed data mapping

---

### Issue #15: Similar Products Showing Wrong Data
**Fixed:** Similar products now work correctly with ML service
- Backend endpoint `/api/products/:id/similar` returns vector-based similar products
- Weaviate generates embeddings on first access (lazy generation)
- ML service uses sentence-transformers for product similarity
**Note:** Requires ML service and Weaviate to be running

---

### Issue #1: Wishlist Button No Visual Feedback
**Fixed:** Added toggle functionality with visual feedback
- Heart icon now fills with red color when product is in wishlist
- Button toggles between add/remove from wishlist
- Uses `useToggleWishlist` and `useIsInWishlist` hooks
**Files Changed:**
- `frontend/hooks/use-wishlist.ts` - Added toggle and check hooks
- `frontend/components/products/product-card.tsx` - Updated heart icon styling
- `frontend/components/products/product-info.tsx` - Updated heart icon styling

---

### Issue #2: Product Card Rating Stars Non-Functional
**Fixed:** Backend now returns `average_rating` and `reviews_count`
- Products service calculates average rating from reviews
- Stars display the actual product rating
**Files Changed:**
- `nestjs-backend/src/products/products.service.ts` - Added rating aggregation

---

### Issue #3: Categories Nav Link Goes to Wrong Page
**Fixed:** Navigation now goes to `/categories` listing page
- Created new categories listing page
- Changed navbar link from `/categories/1` to `/categories`
**Files Changed:**
- `frontend/components/layout/navbar.tsx` - Fixed link
- `frontend/components/layout/mobile-nav.tsx` - Fixed link
- `frontend/app/categories/page.tsx` - Created categories listing page

---

### Issue #4: Products Page Filters Not Working
**Fixed:** Filters now work correctly
- Fixed parameter name mapping (`category_id` → `category`, etc.)
- Category, rating, and stock filters all functional
**Files Changed:**
- `frontend/hooks/use-products.ts` - Fixed parameter mapping

---

### Issue #5: Products Page Missing Pagination Controls
**Fixed:** Pagination now works correctly
- Fixed pagination data transformation from nested `meta` to flat structure
- Pagination controls function properly
**Files Changed:**
- `frontend/hooks/use-products.ts` - Fixed pagination data transformation

---

### Issue #6: Products Page Sorting Not Working
**Fixed:** Sorting now works correctly
- Fixed parameter name mapping (`sort_order` → `sort_dir`)
- Fixed sort field mapping for backend compatibility
**Files Changed:**
- `frontend/hooks/use-products.ts` - Fixed sort parameter mapping

---

### Issue #7: Cart Page Missing Prices, Images, and Broken Totals
**Fixed:** Cart now displays all data correctly
- Backend now returns `product_id`, `price`, `cart_id`, and `images` array
- Order summary totals calculate correctly
**Files Changed:**
- `nestjs-backend/src/cart/cart.service.ts` - Fixed serialization to include all fields

---

### Issue #8: Checkout Page Order Summary Missing Data
**Fixed:** Same fix as Issue #7
- Checkout uses cart data which is now properly structured
**Files Changed:**
- `nestjs-backend/src/cart/cart.service.ts` - Fixed serialization

---

### Issue #9: Checkout Not Pre-Selecting Default Addresses
**Fixed:** Default addresses auto-select on page load
- Added useEffect to auto-select default address when addresses load
- Falls back to first address if only one exists
**Files Changed:**
- `frontend/components/checkout/address-selector.tsx` - Added auto-select logic

---

### Issue #10: "Manage Addresses" Button Not Visually Obvious
**Fixed:** Button now has clear styling
- Added border, hover states, and proper button appearance
**Files Changed:**
- `frontend/components/checkout/checkout-form.tsx` - Updated button styling

---

### Issue #11: Navbar Product Search Not Working
**Fixed:** Implemented debounced search with dropdown
- 300ms debounce on search input
- Dropdown shows search results with product images and prices
- Click to navigate to product detail page
**Files Changed:**
- `frontend/components/layout/search-bar.tsx` - Implemented full search functionality

---

### Issue #13: Wishlist Page Products Missing Images
**Fixed:** Backend now returns images with wishlist items
- Added images array to product select in wishlist query
- Added `product_id` and `user_id` to response
**Files Changed:**
- `nestjs-backend/src/wishlist/wishlist.service.ts` - Added images to product select

---

### Issue #14: My Reviews Page - Product Links Navigate to `products/undefined`
**Fixed:** Backend now returns `product_id` with reviews
- Added `product_id` and `user_id` to serialized review response
**Files Changed:**
- `nestjs-backend/src/reviews/reviews.service.ts` - Added product_id to response

---

### Issue #16: Product Detail Page Rating Stars Not Reflecting Actual Ratings
**Fixed:** Same fix as Issue #2
- Backend returns `average_rating` calculated from reviews
- Both product list and detail pages show correct ratings
**Files Changed:**
- `nestjs-backend/src/products/products.service.ts` - Added rating aggregation

---

### Issue #17: Products Have No SKUs
**Fixed:** Added SKU field to database and API
- Added `sku` field to Prisma schema (nullable, unique)
- Products service includes SKU in responses
- Falls back to `SKU-{product_id}` if not set
**Files Changed:**
- `nestjs-backend/prisma/schema.prisma` - Added sku field
- `nestjs-backend/src/products/products.service.ts` - Added SKU to serialization

**Note:** Run `npx prisma migrate dev` to apply database changes
