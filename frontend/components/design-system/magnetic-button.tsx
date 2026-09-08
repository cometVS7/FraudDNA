"use client";

import React, { useRef, useEffect } from "react";
import Link from "next/link";

interface MagneticButtonProps {
  children: React.ReactNode;
  href?: string;
  onClick?: () => void;
  variant?: "primary" | "secondary" | "ghost" | "glass" | "danger";
  size?: "sm" | "md" | "lg";
  className?: string;
  icon?: React.ReactNode;
  disabled?: boolean;
}

export function MagneticButton({
  children,
  href,
  onClick,
  variant = "primary",
  size = "md",
  className = "",
  icon,
  disabled = false,
}: MagneticButtonProps) {
  const elementRef = useRef<HTMLButtonElement | HTMLAnchorElement | null>(null);
  const rafId = useRef<number | null>(null);
  const targetPos = useRef({ x: 0, y: 0 });
  const currentPos = useRef({ x: 0, y: 0 });
  const isHovered = useRef(false);

  useEffect(() => {
    // Check for reduced motion or coarse pointer (touch devices)
    const isCoarse = window.matchMedia("(pointer: coarse)").matches;
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    if (isCoarse || prefersReducedMotion || !elementRef.current) {
      return;
    }

    const animate = () => {
      // Linear interpolation (lerp) for smooth spring-like pull
      const factor = isHovered.current ? 0.18 : 0.12;
      currentPos.current.x += (targetPos.current.x - currentPos.current.x) * factor;
      currentPos.current.y += (targetPos.current.y - currentPos.current.y) * factor;

      if (elementRef.current) {
        elementRef.current.style.transform = `translate3d(${currentPos.current.x.toFixed(2)}px, ${currentPos.current.y.toFixed(2)}px, 0)`;
      }

      // Continue animating while there's delta or while hovered
      const delta =
        Math.abs(targetPos.current.x - currentPos.current.x) +
        Math.abs(targetPos.current.y - currentPos.current.y);

      if (isHovered.current || delta > 0.05) {
        rafId.current = requestAnimationFrame(animate);
      } else if (elementRef.current) {
        elementRef.current.style.transform = "translate3d(0, 0, 0)";
      }
    };

    const handleMouseMove = (e: Event) => {
      const mouseEvent = e as MouseEvent;
      if (!elementRef.current || disabled) return;
      const rect = elementRef.current.getBoundingClientRect();
      const rawX = mouseEvent.clientX - (rect.left + rect.width / 2);
      const rawY = mouseEvent.clientY - (rect.top + rect.height / 2);

      // Bounded magnetic pull (max 8px)
      const maxPull = 8;
      targetPos.current.x = Math.max(-maxPull, Math.min(maxPull, rawX * 0.2));
      targetPos.current.y = Math.max(-maxPull, Math.min(maxPull, rawY * 0.2));

      if (!isHovered.current) {
        isHovered.current = true;
        if (rafId.current) cancelAnimationFrame(rafId.current);
        rafId.current = requestAnimationFrame(animate);
      }
    };

    const handleMouseLeave = () => {
      isHovered.current = false;
      targetPos.current.x = 0;
      targetPos.current.y = 0;
    };

    const el = elementRef.current;
    el.addEventListener("mousemove", handleMouseMove);
    el.addEventListener("mouseleave", handleMouseLeave);

    return () => {
      el.removeEventListener("mousemove", handleMouseMove);
      el.removeEventListener("mouseleave", handleMouseLeave);
      if (rafId.current) cancelAnimationFrame(rafId.current);
    };
  }, [disabled]);

  const baseStyles =
    "group relative inline-flex items-center justify-center font-medium select-none cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400/60 focus-visible:ring-offset-2 focus-visible:ring-offset-[#06080E] disabled:opacity-50 disabled:pointer-events-none rounded-full transition-shadow duration-300";

  const sizeStyles = {
    sm: "px-3.5 py-1.5 text-xs gap-1.5",
    md: "px-5 py-2.5 text-sm gap-2",
    lg: "px-6 sm:px-7 py-3 sm:py-3.5 text-sm sm:text-base gap-2.5",
  };

  const variantStyles = {
    primary:
      "bg-gradient-to-r from-cyan-400 via-teal-300 to-blue-500 text-[#06080E] font-semibold shadow-[0_4px_20px_rgba(0,229,255,0.25)] hover:shadow-[0_6px_30px_rgba(0,229,255,0.45)] border border-cyan-200/40 active:scale-[0.98]",
    secondary:
      "bg-[#101420]/90 hover:bg-[#161B2C] text-slate-200 hover:text-white border border-white/10 hover:border-cyan-500/30 shadow-[0_4px_16px_rgba(0,0,0,0.4)] active:scale-[0.98]",
    glass:
      "bg-white/[0.04] backdrop-blur-xl hover:bg-white/[0.08] text-white border border-white/12 shadow-[0_4px_20px_rgba(0,0,0,0.3)] hover:border-cyan-400/40 hover:shadow-[0_0_20px_rgba(0,229,255,0.15)] active:scale-[0.98]",
    ghost:
      "bg-transparent text-slate-400 hover:text-white hover:bg-white/5",
    danger:
      "bg-gradient-to-r from-rose-600 to-red-700 text-white font-semibold shadow-[0_4px_20px_rgba(244,63,94,0.3)] hover:shadow-[0_6px_30px_rgba(244,63,94,0.5)] border border-rose-400/30 active:scale-[0.98]",
  };

  const content = (
    <>
      <span className="relative z-10 flex items-center gap-2">
        {children}
        {icon && <span className="transition-transform duration-200 group-hover:translate-x-0.5">{icon}</span>}
      </span>
      {variant === "primary" && (
        <span className="absolute inset-0 rounded-full bg-white/20 opacity-0 group-hover:opacity-100 transition-opacity duration-200 blur-xs" />
      )}
    </>
  );

  if (href) {
    return (
      <Link
        href={href}
        ref={elementRef as React.Ref<HTMLAnchorElement>}
        className={`${baseStyles} ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
      >
        {content}
      </Link>
    );
  }

  return (
    <button
      ref={elementRef as React.Ref<HTMLButtonElement>}
      onClick={onClick}
      disabled={disabled}
      className={`${baseStyles} ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
    >
      {content}
    </button>
  );
}
