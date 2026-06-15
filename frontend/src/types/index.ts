export interface User {
  id: string;
  username: string;
  email: string | null;
  nickname: string | null;
  avatar: string | null;
  role: string;
  disabled?: boolean;
  created_at: string;
}

export interface TokenOut {
  access_token: string;
  token_type: 'bearer';
  expires_at: string;
  user: User;
}

export type LandmarkStatus = 'PENDING' | 'APPROVED' | 'REJECTED';

export interface Landmark {
  id: string;
  owner_id: string;
  name: string;
  category: string;
  description: string;
  image_url: string | null;
  lng: number;
  lat: number;
  status: LandmarkStatus;
  created_at: string;
  updated_at: string;
}

export interface LandmarkCreateIn {
  name: string;
  category: string;
  description?: string;
  image_url?: string | null;
  lng: number;
  lat: number;
}

export type LandmarkUpdateIn = Partial<LandmarkCreateIn> & { status?: LandmarkStatus };

export interface NearbyHit {
  id: string;
  name: string;
  category: string;
  lng: number;
  lat: number;
  distance_km: number;
}

export interface DistanceOut {
  a_id: string;
  b_id: string;
  distance_km: number;
}

export interface FavoriteState {
  landmark_id: string;
  favorited: boolean;
  count: number;
}

export interface Comment {
  id: string;
  landmark_id: string;
  user_id: string;
  username: string;
  content: string;
  created_at: string;
}

export interface ApiError {
  code: string;
  message: string;
}
