/**
 * Integration Contract: God's Eye 3D Campus Map
 * Team KUET_MANTIS - Forkathon 2026
 * 
 * Teammates integrating the map should use these TypeScript definitions
 * to pass data into the map component or handle user selection events.
 */

export type LandmarkCategory = 'academic' | 'residential' | 'hotspot' | 'perimeter_300m' | 'admin';

export interface KUETLandmark {
  id: string;
  name: string;
  category: LandmarkCategory;
  coords: [number, number]; // [Latitude, Longitude]
  floors: number;
  color: string;
  description: string;
  popular_items?: string[];
}

export interface MapItemPin {
  id: string;
  title: string;
  category: 'Chargers' | 'Calculators' | 'Lab Gear' | 'Cables' | 'Drawing' | 'Urgent Requests' | 'Other';
  zone_id: string; // Foreign key matching KUETLandmark.id
  lender_name: string;
  lender_karma: number;
  status: 'available' | 'borrowed' | 'beacon';
  image: string;
  condition: 'Like New' | 'Good' | 'Fair' | 'N/A';
  specs: string;
  tags: string[];
}

export interface GodsEyeMapProps {
  landmarks: KUETLandmark[];
  items: MapItemPin[];
  selectedZoneId?: string;
  activeCategoryFilter?: string;
  onSelectZone: (zone: KUETLandmark) => void;
  onSelectItem: (item: MapItemPin) => void;
  onRequestBorrow: (item: MapItemPin) => void;
}

