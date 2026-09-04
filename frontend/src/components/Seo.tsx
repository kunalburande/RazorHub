import { useEffect } from 'react';

interface SeoProps {
  title: string;
  description?: string;
  image?: string;
  type?: 'website' | 'product';
  jsonLd?: Record<string, any>;
}

function upsertMeta(selector: string, attributes: Record<string, string>) {
  let element = document.head.querySelector<HTMLMetaElement>(selector);
  if (!element) {
    element = document.createElement('meta');
    document.head.appendChild(element);
  }

  Object.entries(attributes).forEach(([key, value]) => {
    element?.setAttribute(key, value);
  });
}

export default function Seo({ title, description = 'RazorHub local marketplace for products, seller stores, delivery, and checkout.', image, type = 'website', jsonLd }: SeoProps) {
  useEffect(() => {
    const fullTitle = title.includes('RazorHub') ? title : `${title} | RazorHub`;
    document.title = fullTitle;

    upsertMeta('meta[name="description"]', { name: 'description', content: description });
    upsertMeta('meta[property="og:title"]', { property: 'og:title', content: fullTitle });
    upsertMeta('meta[property="og:description"]', { property: 'og:description', content: description });
    upsertMeta('meta[property="og:type"]', { property: 'og:type', content: type });
    upsertMeta('meta[name="twitter:card"]', { name: 'twitter:card', content: image ? 'summary_large_image' : 'summary' });

    if (image) {
      upsertMeta('meta[property="og:image"]', { property: 'og:image', content: image });
      upsertMeta('meta[name="twitter:image"]', { name: 'twitter:image', content: image });
    }

    if (jsonLd) {
      let script = document.head.querySelector<HTMLScriptElement>('script[type="application/ld+json"]');
      if (!script) {
        script = document.createElement('script');
        script.type = 'application/ld+json';
        document.head.appendChild(script);
      }
      script.textContent = JSON.stringify(jsonLd);
    }
  }, [description, image, title, type, jsonLd]);

  return null;
}
