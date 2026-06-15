import type { RoutePlan } from '@/types';

const TK = import.meta.env.VITE_TIANDITU_KEY as string | undefined;

// 驾车策略：0 最快、1 最短、2 避开高速
export type DriveStyle = '0' | '1' | '2';

/**
 * 天地图驾车路径规划。直接从浏览器调用(接口返回 CORS *)，解析返回的 XML，
 * 取出路径点串、总距离与时长。orig/dest 为 WGS-84 [lng, lat]。
 */
export async function planDrive(
  orig: [number, number],
  dest: [number, number],
  style: DriveStyle = '0',
): Promise<RoutePlan> {
  if (!TK) throw new Error('未配置天地图 key，无法进行路径规划');

  const postStr = JSON.stringify({
    orig: `${orig[0]},${orig[1]}`,
    dest: `${dest[0]},${dest[1]}`,
    style,
  });
  const url =
    `https://api.tianditu.gov.cn/drive?postStr=${encodeURIComponent(postStr)}` +
    `&type=search&tk=${TK}`;

  const resp = await fetch(url);
  const text = await resp.text();
  const doc = new DOMParser().parseFromString(text, 'text/xml');

  // 接口异常时返回 <error>，没有 routelatlon
  const latlon = doc.querySelector('routelatlon')?.textContent?.trim();
  if (!latlon) {
    const msg = doc.querySelector('error, msg')?.textContent || '路径规划失败（可能被限流，请稍后再试）';
    throw new Error(msg);
  }

  const points = latlon.split(';').reduce<[number, number][]>((acc, pair) => {
    const [lng, lat] = pair.split(',').map(Number);
    if (Number.isFinite(lng) && Number.isFinite(lat)) acc.push([lat, lng]);
    return acc;
  }, []);

  const distance = Number(doc.querySelector('distance')?.textContent ?? '0'); // km
  const duration = Number(doc.querySelector('duration')?.textContent ?? '0'); // 秒

  return {
    points,
    distance_km: Math.round(distance * 100) / 100,
    duration_min: Math.round(duration / 60),
  };
}
