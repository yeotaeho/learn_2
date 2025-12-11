declare namespace kakao.maps {
  class LatLng {
    constructor(lat: number, lng: number);
    getLat(): number;
    getLng(): number;
  }

  class Map {
    constructor(container: HTMLElement, options: MapOptions);
    setCenter(latlng: LatLng): void;
    setLevel(level: number): void;
    getCenter(): LatLng;
    getLevel(): number;
  }

  interface MapOptions {
    center: LatLng;
    level: number;
  }

  class Circle {
    constructor(options: CircleOptions);
    setMap(map: Map | null): void;
    getMap(): Map | null;
  }

  interface CircleOptions {
    center: LatLng;
    radius: number;
    strokeWeight?: number;
    strokeColor?: string;
    strokeOpacity?: number;
    fillColor?: string;
    fillOpacity?: number;
  }

  class CustomOverlay {
    constructor(options: CustomOverlayOptions);
    setMap(map: Map | null): void;
    getMap(): Map | null;
  }

  interface CustomOverlayOptions {
    position: LatLng;
    content: string;
    yAnchor?: number;
    xAnchor?: number;
  }

  namespace maps {
    function load(callback: () => void): void;
  }
}

declare namespace window {
  interface Window {
    kakao: {
      maps: {
        LatLng: typeof kakao.maps.LatLng;
        Map: typeof kakao.maps.Map;
        Circle: typeof kakao.maps.Circle;
        CustomOverlay: typeof kakao.maps.CustomOverlay;
        load: (callback: () => void) => void;
      };
    };
  }
}

