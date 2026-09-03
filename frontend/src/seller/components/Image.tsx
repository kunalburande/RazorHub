import { useState } from "react";
import { cn } from "../utils/cn";

interface Props {
  imageSrc?: string;
  altText?: string;
  className?: string;
  categoryName?: string;
}

const CATEGORY_FALLBACKS: Record<string, string> = {
  electronics: "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=800&q=80",
  clothes: "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=800&q=80",
  photography: "https://images.unsplash.com/photo-1502920917128-1aa500764cbd?auto=format&fit=crop&w=800&q=80",
  furniture: "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?auto=format&fit=crop&w=800&q=80",
  sneakers: "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=800&q=80",
  default: "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=800&q=80",
};

const Image = ({ imageSrc, altText, className, categoryName }: Props) => {
  const [hasError, setHasError] = useState(false);

  const getFallback = () => {
    const cat = (categoryName || "").toLowerCase();
    if (cat.includes("electr")) return CATEGORY_FALLBACKS.electronics;
    if (cat.includes("cloth") || cat.includes("apparel")) return CATEGORY_FALLBACKS.clothes;
    if (cat.includes("photo") || cat.includes("camera")) return CATEGORY_FALLBACKS.photography;
    if (cat.includes("furn")) return CATEGORY_FALLBACKS.furniture;
    if (cat.includes("shoe") || cat.includes("sneak")) return CATEGORY_FALLBACKS.sneakers;
    return CATEGORY_FALLBACKS.default;
  };

  const finalSrc = hasError || !imageSrc ? getFallback() : imageSrc;

  return (
    <div className={cn("relative overflow-hidden bg-gray-100 dark:bg-slate-800", className)}>
      <img
        src={finalSrc}
        alt={altText || "Product"}
        className="h-full w-full object-cover object-center transition-transform duration-300 group-hover:scale-105"
        loading="lazy"
        onError={() => {
          if (!hasError) setHasError(true);
        }}
      />
    </div>
  );
};

export default Image;
