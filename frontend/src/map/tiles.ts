import L from 'leaflet';

// 天地图 key：从 .env 读取(VITE_TIANDITU_KEY)，不硬编码进源码。
const TK = import.meta.env.VITE_TIANDITU_KEY as string | undefined;

export const usingCompliantMap = !!TK;

/**
 * 给地图挂底图层。
 * 配置了天地图 key 时使用天地图(国家官方、边界合规含台湾/南海断续线，
 * 且为 WGS-84 真实坐标，与后端存储的经纬度天然对齐)；否则临时回退 OSM。
 */
export function addBaseLayers(map: L.Map): void {
  if (TK) {
    const subdomains = ['0', '1', '2', '3', '4', '5', '6', '7'];
    const wmts = (layer: string) =>
      `https://t{s}.tianditu.gov.cn/${layer}_w/wmts?SERVICE=WMTS&REQUEST=GetTile` +
      `&VERSION=1.0.0&LAYER=${layer}&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles` +
      `&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=${TK}`;

    // 矢量底图 + 矢量注记(地名标注)
    L.tileLayer(wmts('vec'), {
      subdomains,
      maxZoom: 18,
      attribution: '© 天地图',
    }).addTo(map);
    L.tileLayer(wmts('cva'), { subdomains, maxZoom: 18 }).addTo(map);
  } else {
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '© OpenStreetMap contributors',
    }).addTo(map);
  }
}
