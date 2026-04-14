/**
 * EraPet — Animated virtual pet that strolls along the bottom of the screen.
 *
 * Behaviors:
 * - Idle: stands still, slight breathing animation
 * - Walking: strolls left/right across the bottom
 * - Waving: waves when hovered
 * - Thinking: when AI is processing
 * - Speaking: when AI response arrives
 * - Click: opens chat widget
 */

import { useState, useEffect, useCallback, useRef } from "react";
import { EraAvatar } from "./EraAvatar";

type PetState = "idle" | "walking" | "waving" | "thinking" | "speaking";

interface EraPetProps {
  onChatOpen: () => void;
  isChatOpen: boolean;
  isThinking?: boolean;
  isSpeaking?: boolean;
}

export function EraPet({ onChatOpen, isChatOpen, isThinking = false, isSpeaking = false }: EraPetProps) {
  const [state, setState] = useState<PetState>("idle");
  const [x, setX] = useState(80); // percentage from left (0-90)
  const [direction, setDirection] = useState<"left" | "right">("left");
  const [isHovered, setIsHovered] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const animRef = useRef<number | null>(null);
  const walkTargetRef = useRef<number>(80);
  const walkSpeedRef = useRef<number>(0.05);

  // Override state from parent (AI processing)
  useEffect(() => {
    if (isThinking) {
      setState("thinking");
    } else if (isSpeaking) {
      setState("speaking");
    }
  }, [isThinking, isSpeaking]);

  // Walking animation loop
  const animateWalk = useCallback(() => {
    setX((currentX) => {
      const target = walkTargetRef.current;
      const speed = walkSpeedRef.current;
      const diff = target - currentX;

      if (Math.abs(diff) < 0.5) {
        // Arrived at destination
        setState("idle");
        return target;
      }

      return currentX + Math.sign(diff) * speed;
    });

    if (state === "walking") {
      animRef.current = requestAnimationFrame(animateWalk);
    }
  }, [state]);

  useEffect(() => {
    if (state === "walking") {
      animRef.current = requestAnimationFrame(animateWalk);
    }
    return () => {
      if (animRef.current) cancelAnimationFrame(animRef.current);
    };
  }, [state, animateWalk]);

  // Random behavior scheduler
  useEffect(() => {
    if (isChatOpen) return; // Don't stroll when chat is open

    const scheduleBehavior = () => {
      const delay = 3000 + Math.random() * 5000; // 3-8 seconds
      timerRef.current = setTimeout(() => {
        if (isThinking || isSpeaking || isHovered) {
          scheduleBehavior();
          return;
        }

        // Pick random behavior
        const roll = Math.random();
        if (roll < 0.6) {
          // Walk to random position
          const target = 5 + Math.random() * 85; // 5-90%
          walkTargetRef.current = target;
          walkSpeedRef.current = 0.03 + Math.random() * 0.04; // variable speed
          setDirection(target > x ? "right" : "left");
          setState("walking");
        } else if (roll < 0.8) {
          // Wave briefly
          setState("waving");
          setTimeout(() => setState("idle"), 2000);
        } else {
          // Stay idle
          setState("idle");
        }

        scheduleBehavior();
      }, delay);
    };

    scheduleBehavior();
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [isChatOpen, isThinking, isSpeaking, isHovered, x]);

  // Hide when chat panel is open
  if (isChatOpen) return null;

  return (
    <div
      className="fixed bottom-2 z-30 transition-transform duration-75"
      style={{ left: `${x}%` }}
      onMouseEnter={() => {
        setIsHovered(true);
        if (state === "walking") {
          setState("idle");
        }
        setState("waving");
      }}
      onMouseLeave={() => {
        setIsHovered(false);
        setState("idle");
      }}
      onClick={() => {
        setState("idle");
        onChatOpen();
      }}
      role="button"
      aria-label="ERA AI assistant — click to chat"
    >
      {/* Speech bubble on hover */}
      {isHovered && (
        <div className="absolute -top-10 left-1/2 -translate-x-1/2 bg-white border border-slate-200 rounded-lg px-3 py-1.5 shadow-md whitespace-nowrap animate-fade-in">
          <p className="text-xs text-text-primary font-medium">Click to chat!</p>
          <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-px">
            <div className="w-2 h-2 bg-white border-r border-b border-slate-200 rotate-45" />
          </div>
        </div>
      )}

      {/* Online indicator */}
      <div className="absolute -top-1 right-0 h-3 w-3 rounded-full bg-status-success border-2 border-white z-10" />

      <div className="cursor-pointer">
        <EraAvatar
          size={50}
          walking={state === "walking"}
          thinking={state === "thinking"}
          speaking={state === "speaking"}
          waving={state === "waving"}
          direction={direction}
        />
      </div>

      {/* Shadow under the pet */}
      <div
        className="absolute bottom-0 left-1/2 -translate-x-1/2 w-10 h-2 rounded-full bg-black/10 blur-sm"
        style={{ transform: "translateX(-50%)" }}
      />
    </div>
  );
}
