import client from './client';
import type { TokenOut, User } from '@/types';

export interface RegisterPayload {
  username: string;
  email: string;
  password: string;
  nickname?: string;
}

export interface LoginPayload {
  username: string;
  password: string;
}

export const register = (payload: RegisterPayload) =>
  client.post<User>('/auth/register', payload).then((r) => r.data);

export const login = (payload: LoginPayload) =>
  client.post<TokenOut>('/auth/login', payload).then((r) => r.data);

export const logout = () => client.post<void>('/auth/logout').then((r) => r.data);

export const me = () => client.get<User>('/users/me').then((r) => r.data);

export const updateMe = (payload: Partial<Pick<User, 'nickname' | 'avatar_url'>>) =>
  client.patch<User>('/users/me', payload).then((r) => r.data);
