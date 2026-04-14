interface EraAvatarProps {
  size?: number;
  speaking?: boolean;
  thinking?: boolean;
}

export function EraAvatar({ size = 48, speaking = false, thinking = false }: EraAvatarProps) {
  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg viewBox="0 0 100 100" width={size} height={size} className="drop-shadow-lg">
        {/* Head */}
        <circle cx="50" cy="45" r="30" fill="#0A66C2" className="transition-all duration-300" />

        {/* Face plate */}
        <ellipse cx="50" cy="48" rx="24" ry="20" fill="#0F172A" />

        {/* Eyes */}
        <g className={speaking ? "animate-pulse" : ""}>
          <ellipse cx="39" cy="43" rx="4" ry={thinking ? 2 : 5} fill="#0EA5E9"
            className="transition-all duration-300">
            {speaking && <animate attributeName="ry" values="5;3;5" dur="0.4s" repeatCount="indefinite" />}
          </ellipse>
          <ellipse cx="61" cy="43" rx="4" ry={thinking ? 2 : 5} fill="#0EA5E9"
            className="transition-all duration-300">
            {speaking && <animate attributeName="ry" values="5;3;5" dur="0.4s" repeatCount="indefinite" />}
          </ellipse>
        </g>

        {/* Eye shine */}
        <circle cx="37" cy="41" r="1.5" fill="white" opacity="0.8" />
        <circle cx="59" cy="41" r="1.5" fill="white" opacity="0.8" />

        {/* Mouth */}
        {speaking ? (
          <ellipse cx="50" cy="56" rx="6" ry="3" fill="#0EA5E9" opacity="0.6">
            <animate attributeName="ry" values="3;1;3" dur="0.3s" repeatCount="indefinite" />
          </ellipse>
        ) : (
          <path d="M 42 55 Q 50 60 58 55" stroke="#0EA5E9" strokeWidth="2" fill="none" opacity="0.6" />
        )}

        {/* Antenna */}
        <line x1="50" y1="15" x2="50" y2="8" stroke="#0A66C2" strokeWidth="2" />
        <circle cx="50" cy="6" r="3" fill="#0EA5E9">
          {thinking && <animate attributeName="opacity" values="1;0.3;1" dur="1s" repeatCount="indefinite" />}
        </circle>

        {/* Ears / side panels */}
        <rect x="17" y="38" width="5" height="12" rx="2" fill="#0A66C2" />
        <rect x="78" y="38" width="5" height="12" rx="2" fill="#0A66C2" />

        {/* Body hint */}
        <path d="M 35 74 Q 50 82 65 74" stroke="#0A66C2" strokeWidth="3" fill="none" />

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
      </svg>

      {/* Glow effect when active */}
      {(speaking || thinking) && (
        <div className="absolute inset-0 rounded-full animate-ping opacity-20"
          style={{ backgroundColor: "#0EA5E9", animationDuration: "2s" }} />
      )}
    </div>
  );
}
