// Checkout utilities, promo codes, and location lookup

export const promoCodes: Record<string, number> = {
  WELCOME10: 10,
  RAZOR500: 15,
  FESTIVE15: 15,
};

export function resolvePromoCode(code: string): { code: string; valid: boolean } {
  const normalized = (code || '').trim().toUpperCase();
  if (!normalized) {
    return { code: '', valid: false };
  }

  if (normalized in promoCodes) {
    return { code: normalized, valid: true };
  }

  return { code: '', valid: false };
}

export function getCitySuggestions(query: string): string[] {
  const q = (query || '').toLowerCase().trim();
  if (!q) return [];
  const CITIES = [
    'Delhi', 'Mumbai', 'Bengaluru', 'Hyderabad', 'Chennai', 'Kolkata', 'Pune', 'Ahmedabad',
    'Jaipur', 'Surat', 'Lucknow', 'Kanpur', 'Nagpur', 'Indore', 'Thane', 'Bhopal',
    'Visakhapatnam', 'Pimpri-Chinchwad', 'Patna', 'Vadodara', 'Ghaziabad', 'Ludhiana', 'Agra',
    'Nashik', 'Ranchi', 'Faridabad', 'Meerut', 'Rajkot', 'Kalyan-Dombivli', 'Vasai-Virar',
    'Varanasi', 'Srinagar', 'Aurangabad', 'Dhanbad', 'Amritsar', 'Navi Mumbai', 'Allahabad',
    'Howrah', 'Gwalior', 'Jabalpur', 'Coimbatore', 'Vijayawada', 'Jodhpur', 'Madurai', 'Raipur',
  ];
  return CITIES.filter((c) => c.toLowerCase().includes(q)).slice(0, 5);
}
