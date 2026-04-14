interface EraAvatarProps {
  size?: number;
  speaking?: boolean;
  thinking?: boolean;
  walking?: boolean;
  direction?: "left" | "right";
  waving?: boolean;
}

export function EraAvatar({
  size = 48,
  speaking = false,
  thinking = false,
  walking = false,
  direction = "right",
  waving = false,
}: EraAvatarProps) {
  const flip = direction === "left" ? "scale(-1, 1)" : "";

  return (
    <div className="relative" style={{ width: size, height: size * 1.4 }}>
      <svg
        viewBox="0 0 100 140"
        width={size}
        height={size * 1.4}
        className="drop-shadow-lg"
        style={{ transform: flip }}
      >
        {/* ── Body ──────────────────────────── */}
        <rect x="35" y="72" width="30" height="25" rx="6" fill="#0A66C2" />
        <circle cx="50" cy="84" r="3" fill="#0EA5E9" opacity="0.6">
          <animate attributeName="opacity" values="0.6;1;0.6" dur="2s" repeatCount="indefinite" />
        </circle>

        {/* ── Arms ──────────────────────────── */}
        {waving ? (
          <>
            <g transform-origin="65 76">
              <animateTransform attributeName="transform" type="rotate" values="-10,65,76;-40,65,76;-10,65,76" dur="0.6s" repeatCount="indefinite" />
              <rect x="63" y="76" width="6" height="20" rx="3" fill="#0A66C2" />
              <circle cx="66" cy="98" r="4" fill="#0F172A" />
            </g>
            <rect x="31" y="78" width="6" height="18" rx="3" fill="#0A66C2" />
            <circle cx="34" cy="98" r="4" fill="#0F172A" />
          </>
        ) : (
          <>
            <g>
              {walking && (
                <animateTransform attributeName="transform" type="rotate" values="10,34,78;-10,34,78;10,34,78" dur="0.5s" repeatCount="indefinite" />
              )}
              <rect x="24" y="78" width="6" height="18" rx="3" fill="#0A66C2" />
              <circle cx="27" cy="98" r="4" fill="#0F172A" />
            </g>
            <g>
              {walking && (
                <animateTransform attributeName="transform" type="rotate" values="-10,66,78;10,66,78;-10,66,78" dur="0.5s" repeatCount="indefinite" />
              )}
              <rect x="70" y="78" width="6" height="18" rx="3" fill="#0A66C2" />
              <circle cx="73" cy="98" r="4" fill="#0F172A" />
            </g>
          </>
        )}

        {/* ── Legs ──────────────────────────── */}
        <g>
          {walking && (
            <animateTransform attributeName="transform" type="rotate" values="15,42,97;-15,42,97;15,42,97" dur="0.4s" repeatCount="indefinite" />
          )}
          <rect x="38" y="95" width="8" height="20" rx="4" fill="#0F172A" />
          <ellipse cx="42" cy="117" rx="7" ry="4" fill="#0A66C2" />
        </g>
        <g>
          {walking && (
            <animateTransform attributeName="transform" type="rotate" values="-15,58,97;15,58,97;-15,58,97" dur="0.4s" repeatCount="indefinite" />
          )}
          <rect x="54" y="95" width="8" height="20" rx="4" fill="#0F172A" />
          <ellipse cx="58" cy="117" rx="7" ry="4" fill="#0A66C2" />
        </g>

        {/* ── Head ──────────────────────────── */}
        <circle cx="50" cy="45" r="28" fill="#0A66C2" />
        <ellipse cx="50" cy="48" rx="22" ry="18" fill="#0F172A" />

        {/* Eyes */}
        <ellipse cx="40" cy="44" rx="4" ry={thinking ? 2 : 5} fill="#0EA5E9" className="transition-all duration-300">
          {speaking && <animate attributeName="ry" values="5;3;5" dur="0.4s" repeatCount="indefinite" />}
        </ellipse>
        <ellipse cx="60" cy="44" rx="4" ry={thinking ? 2 : 5} fill="#0EA5E9" className="transition-all duration-300">
          {speaking && <animate attributeName="ry" values="5;3;5" dur="0.4s" repeatCount="indefinite" />}
        </ellipse>
        <circle cx="38" cy="42" r="1.5" fill="white" opacity="0.8" />
        <circle cx="58" cy="42" r="1.5" fill="white" opacity="0.8" />

        {/* Mouth */}
        {speaking ? (
          <ellipse cx="50" cy="56" rx="6" ry="3" fill="#0EA5E9" opacity="0.6">
            <animate attributeName="ry" values="3;1;3" dur="0.3s" repeatCount="indefinite" />
          </ellipse>
        ) : (
          <path d="M 43 55 Q 50 59 57 55" stroke="#0EA5E9" strokeWidth="2" fill="none" opacity="0.6" />
        )}

        {/* Antenna */}
        <line x1="50" y1="17" x2="50" y2="8" stroke="#0A66C2" strokeWidth="2" />
        <circle cx="50" cy="6" r="3" fill="#0EA5E9">
          {thinking && <animate attributeName="opacity" values="1;0.3;1" dur="1s" repeatCount="indefinite" />}
          {walking && <animate attributeName="cy" values="6;4;6" dur="0.4s" repeatCount="indefinite" />}
        </circle>

        {/* Ears */}
        <rect x="19" y="38" width="5" height="12" rx="2" fill="#0A66C2" />
        <rect x="76" y="38" width="5" height="12" rx="2" fill="#0A66C2" />

        {/* Thinking dots */}
        {thinking && (
          <g>
            <circle cx="40" cy="56" r="1.5" fill="#0EA5E9">
              <animate attributeName="opacity" values="0;1;0" dur="1.2s" begin="0s" repeatCount="indefinite" />
            </circle>
            <circle cx="50" cy="56" r="1.5" fill="#0EA5E9">
              <animate attributeName="opacity" values="0;1;0" dur="1.2s" begin="0.3s" repeatCount="indefinite" />
            </circle>
            <circle cx="60" cy="56" r="1.5" fill="#0EA5E9">
              <animate attributeName="opacity" values="0;1;0" dur="1.2s" begin="0.6s" repeatCount="indefinite" />
            </circle>
          </g>
        )}

        {/* Body bounce when walking */}
        {walking && (
          <animateTransform attributeName="transform" type="translate" values="0,0;0,-2;0,0" dur="0.2s" repeatCount="indefinite" />
        )}
      </svg>
    </div>
  );
}
