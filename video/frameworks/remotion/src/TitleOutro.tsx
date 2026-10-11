import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';

/**
 * Титры/аутро в каноне YurichHub.
 *
 * Токены и правила — brand/YURICHHUB-STYLE.md: тёмный дом #0A0A0A, знак YURICH чернилами
 * и HUB лаймом, обводка Oswald, подпись Inter, фиксированные свечения и зерно.
 * Движение — по скиллу emil/animate: только transform и opacity, ease-out, без отскока.
 */
const C = {
  bg: '#0A0A0A',
  ink: '#F3F1EA',
  lime: '#D7FF3D',
  gold: '#C8A24A',
  dim: '#8C8C8C',
  body: '#C4C4C4',
  line: 'rgba(243,241,234,0.14)',
};

export const TitleOutro: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, width } = useVideoConfig();

  // Вход знака: только y и opacity, ease-out, 0.6s — как на постерах.
  const markSpring = spring({ frame, fps, config: { damping: 200 }, durationInFrames: 20 });
  const markY = interpolate(markSpring, [0, 1], [110, 0]);
  const markOpacity = interpolate(markSpring, [0, 1], [0, 1]);

  const ruleScale = interpolate(frame, [8, 26], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const coordsOpacity = interpolate(frame, [22, 40], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const coordsY = interpolate(frame, [22, 40], [22, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const footerScale = interpolate(frame, [40, 62], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const footerOpacity = interpolate(frame, [52, 70], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  return (
    <AbsoluteFill style={{ backgroundColor: C.bg, fontFamily: 'Inter, sans-serif' }}>
      {/* Свечения: фиксированные, лайм слева сверху и золото справа снизу, opacity 0.05 */}
      <AbsoluteFill>
        <svg width="100%" height="100%" viewBox="0 0 1920 1080" preserveAspectRatio="none">
          <ellipse cx="288" cy="96" rx="840" ry="504" fill={C.lime} opacity="0.05" />
          <ellipse cx="1704" cy="1032" rx="864" ry="528" fill={C.gold} opacity="0.05" />
        </svg>
      </AbsoluteFill>

      {/* Зерно: те же параметры, что в render.js — baseFrequency 0.9, две октавы, 0.07 */}
      <AbsoluteFill
        style={{
          opacity: 0.07,
          backgroundImage:
            "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='320' height='320'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/><feColorMatrix type='saturate' values='0'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>\")",
          backgroundSize: '320px 320px',
        }}
      />

      <div style={{ position: 'absolute', left: 84, top: 372 }}>
        <div
          style={{
            width: 96,
            height: 2,
            backgroundColor: C.lime,
            transform: `scaleX(${ruleScale})`,
            transformOrigin: 'left center',
          }}
        />
        <div
          style={{
            marginTop: 34,
            transform: `translateY(${markY}px)`,
            opacity: markOpacity,
            fontFamily: 'Oswald, sans-serif',
            fontWeight: 700,
            fontSize: 190,
            letterSpacing: 2,
            lineHeight: 1,
            color: C.ink,
            // Канон: обводка Oswald — 2.8% кегля, цветом заливки (см. YURICHHUB-STYLE.md)
            WebkitTextStroke: `${(190 * 0.028).toFixed(1)}px ${C.ink}`,
          }}
        >
          {/* HUB лаймом, но обводка у него своя — иначе белая обводка съест лайм */}
          YURICH
          <span style={{ color: C.lime, WebkitTextStroke: `${(190 * 0.028).toFixed(1)}px ${C.lime}` }}>HUB</span>
        </div>
      </div>

      <div
        style={{
          position: 'absolute',
          left: 84,
          top: 760,
          fontFamily: 'Archivo, sans-serif',
          fontWeight: 600,
          fontSize: 26,
          letterSpacing: 6,
          color: C.body,
          textTransform: 'uppercase',
          transform: `translateY(${coordsY}px)`,
          opacity: coordsOpacity,
        }}
      >
        44.6167° N · 33.5258° E
      </div>
      <div
        style={{
          position: 'absolute',
          left: 84,
          top: 806,
          fontFamily: 'Inter, sans-serif',
          fontSize: 21,
          letterSpacing: 3,
          color: C.dim,
          textTransform: 'uppercase',
          opacity: coordsOpacity,
        }}
      >
        Sevastopol · Black Sea · Est. 2026
      </div>

      <div style={{ position: 'absolute', left: 84, top: 974, width: width - 168 }}>
        <div
          style={{
            height: 2,
            backgroundColor: C.line,
            transform: `scaleX(${footerScale})`,
            transformOrigin: 'left center',
          }}
        />
      </div>
      <div
        style={{
          position: 'absolute',
          left: 84,
          top: 1008,
          opacity: footerOpacity,
          fontFamily: 'Oswald, sans-serif',
          fontWeight: 700,
          fontSize: 26,
          letterSpacing: 1.2,
          color: C.ink,
        }}
      >
        YURICH<span style={{ color: C.lime }}>HUB</span>
      </div>
      <div
        style={{
          position: 'absolute',
          right: 84,
          top: 1014,
          opacity: footerOpacity,
          fontFamily: 'Archivo, sans-serif',
          fontSize: 20,
          letterSpacing: 2,
          color: C.dim,
        }}
      >
        motion · remotion
      </div>
    </AbsoluteFill>
  );
};
