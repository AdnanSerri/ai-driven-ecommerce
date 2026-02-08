export interface User {
  id: number;
  name: string;
  email: string;
  phone?: string;
  avatar?: string;
  date_of_birth?: string;
  preferences?: Record<string, unknown>;
  email_verified_at?: string;
  created_at: string;
  updated_at: string;
}

export interface Category {
  id: number;
  name: string;
  slug: string;
  description?: string;
  parent_id?: number;
  image?: string;
  children?: Category[];
  products_count?: number;
  created_at: string;
  updated_at: string;
}

export interface ProductImage {
  id: number;
  product_id: number;
  url: string;
  alt_text?: string;
  sort_order: number;
  is_primary: boolean;
}

export interface Product {
  id: number;
  name: string;
  slug: string;
  description: string;
  price: number;
  compare_at_price?: number;
  sku: string;
  stock_quantity: number;
  is_active: boolean;
  category_id: number;
  category?: Category;
  images: ProductImage[];
  average_rating?: number;
  reviews_count?: number;
  created_at: string;
  updated_at: string;
}

export interface CartItem {
  id: number;
  cart_id: number;
  product_id: number;
  quantity: number;
  price: number;
  product: Product;
  created_at: string;
  updated_at: string;
}

export interface Cart {
  id: number;
  user_id: number;
  items: CartItem[];
  total: number;
  items_count: number;
  created_at: string;
  updated_at: string;
}

export interface Address {
  id: number;
  user_id: number;
  label?: string;
  type: "shipping" | "billing";
  first_name: string;
  last_name: string;
  address_line_1: string;
  address_line_2?: string;
  city: string;
  state: string;
  postal_code: string;
  country: string;
  phone?: string;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface OrderItem {
  id: number;
  product_name: string;
  product_price: number;
  quantity: number;
  subtotal: number;
  product?: {
    id: number;
    name: string;
    price: number;
    image_url?: string;
  };
}

export interface Order {
  id: number;
  user_id: number;
  order_number: string;
  status: "pending" | "confirmed" | "processing" | "shipped" | "delivered" | "cancelled";
  subtotal: number;
  discount: number;
  tax: number;
  total: number;
  notes?: string;
  shipping_address: Address;
  billing_address: Address;
  items: OrderItem[];
  ordered_at: string;
}

export interface Review {
  id: number;
  user_id: number;
  product_id: number;
  rating: number;
  title?: string;
  comment: string;
  sentiment?: "positive" | "negative" | "neutral";
  sentiment_score?: number;
  is_verified_purchase: boolean;
  user?: User;
  product?: Product;
  created_at: string;
  updated_at: string;
}

export interface WishlistItem {
  id: number;
  user_id: number;
  product_id: number;
  product: Product;
  created_at: string;
}

export interface PersonalityDimension {
  name: string;
  score: number;
  description: string;
}

export interface PersonalityProfile {
  user_id: number;
  personality_type: string;
  dimensions: Record<string, number>;
  confidence: number;
  data_points: number;
  last_updated: string;
}

export interface PersonalityTraits {
  personality_type: string;
  dimensions: PersonalityDimension[];
  traits: string[];
  recommendations_impact: {
    product_selection: string;
    pricing: string;
    categories: string;
  };
}

export interface Recommendation {
  product: Product;
  score: number;
  reason?: string;
}

export interface FrequentlyBoughtTogetherItem {
  product_id: number;
  name: string;
  price: number | null;
  image_url: string | null;
  category_id: number | null;
  category_name: string | null;
  co_occurrence_count: number;
  in_stock: boolean;
}

export interface FrequentlyBoughtTogetherResponse {
  success: boolean;
  product_id: number;
  products: FrequentlyBoughtTogetherItem[];
  total: number;
  bundle_total: number | null;
}

export interface TrendingProductItem {
  product_id: number;
  name: string;
  price: number | null;
  image_url: string | null;
  category_id: number | null;
  category_name: string | null;
  trending_score: number;
  recent_orders: number;
  recent_views: number;
  growth_rate: number | null;
  in_stock: boolean;
}

export interface TrendingProductsResponse {
  success: boolean;
  products: TrendingProductItem[];
  total: number;
  category_id: number | null;
  period_days: number;
}

export interface SimilarProductItem {
  id: number;
  name: string;
  price: number;
  image_url: string | null;
  category: string | null;
  in_stock: boolean;
}

export interface SimilarProduct {
  product: SimilarProductItem;
  similarity_score: number | null;
}

export interface PaginatedResponse<T> {
  data: T[];
  current_page: number;
  last_page: number;
  per_page: number;
  total: number;
  from: number;
  to: number;
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface ProductFilters {
  search?: string;
  category_id?: number;
  min_price?: number;
  max_price?: number;
  min_rating?: number;
  in_stock?: boolean;
  sort_by?: "name" | "price" | "created_at" | "stock_quantity";
  sort_order?: "asc" | "desc";
  page?: number;
}
