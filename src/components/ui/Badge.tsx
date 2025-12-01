import * as React from "react"

// Hardcoded variants to avoid dependencies
const VARIANTS = {
  default: "border-transparent bg-primary text-primary-foreground hover:bg-primary/80",
  secondary: "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
  destructive: "border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80",
  outline: "text-foreground",
  success: "border-transparent bg-emerald-600 text-white hover:bg-emerald-700",
  warning: "border-transparent bg-amber-500 text-white hover:bg-amber-600",
  error: "border-transparent bg-red-600 text-white hover:bg-red-700",
};

const SIZES = {
  default: "px-2.5 py-0.5 text-xs",
  sm: "px-2 py-0.5 text-[10px]",
  lg: "px-3 py-1 text-sm",
};

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: keyof typeof VARIANTS;
  size?: keyof typeof SIZES;
}

function Badge({ className, variant = "default", size = "default", ...props }: BadgeProps) {
  const vClass = VARIANTS[variant] || VARIANTS.default;
  const sClass = SIZES[size] || SIZES.default;
  
  return (
    <div 
      className={`inline-flex items-center rounded-full border font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 ${vClass} ${sClass} ${className || ""}`} 
      {...props} 
    />
  )
}

Badge.displayName = "Badge"

export { Badge }