"use client";

import { motion, useSpring, useTransform } from "framer-motion";
import { useEffect } from "react";

/**
 * AnimatedNumber smoothly interpolates between values using framer-motion springs.
 * It gives a professional, "alive" feeling to rapidly changing telemetry or KPIs.
 */
export function AnimatedNumber({ value, format = (v) => Math.round(v).toString(), className }) {
  const spring = useSpring(value, { mass: 0.5, stiffness: 60, damping: 15 });
  const display = useTransform(spring, (current) => format(current));

  useEffect(() => {
    spring.set(value);
  }, [spring, value]);

  return <motion.span className={className}>{display}</motion.span>;
}
