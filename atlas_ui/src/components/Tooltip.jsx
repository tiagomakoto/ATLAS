// atlas_ui/src/components/Tooltip.jsx
import React, { useState, useEffect, useRef } from "react";

export default function Tooltip({ 
  children, 
  content, 
  delay = 600, 
  position = "bottom", 
  maxWidth = 280 
}) {
  const [visible, setVisible] = useState(false);
  const [coords, setCoords] = useState({ x: 0, y: 0 });
  const [adjustedPosition, setAdjustedPosition] = useState(position);
  const triggerRef = useRef(null);
  const timeoutRef = useRef(null);

  const showTooltip = (e) => {
    timeoutRef.current = setTimeout(() => {
      const rect = triggerRef.current?.getBoundingClientRect();
      if (rect) {
        const tooltipWidth = maxWidth;
        const tooltipHeight = 120; // estimativa
        const padding = 16;

        // Calcular posição inicial
        let x = rect.left + rect.width / 2;
        let y = rect.top;
        let newPos = position;

        // ✅ Ajustar horizontalmente se ultrapassar direita
        if (x + tooltipWidth / 2 > window.innerWidth - padding) {
          x = window.innerWidth - tooltipWidth / 2 - padding;
        }
        // ✅ Ajustar horizontalmente se ultrapassar esquerda
        if (x - tooltipWidth / 2 < padding) {
          x = tooltipWidth / 2 + padding;
        }

        // ✅ Ajustar verticalmente se ultrapassar embaixo
        if (y + tooltipHeight > window.innerHeight - padding) {
          y = rect.top - tooltipHeight - 8;
          newPos = "top";
        }
        // ✅ Ajustar verticalmente se ultrapassar em cima
        if (y - tooltipHeight < padding) {
          y = rect.bottom + 8;
          newPos = "bottom";
        }

        setCoords({ x, y });
        setAdjustedPosition(newPos);
      }
      setVisible(true);
    }, delay);
  };

  const hideTooltip = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    setVisible(false);
  };

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const getPositionStyles = () => {
    const baseStyles = {
      position: "fixed",
      left: `${coords.x}px`,
      top: `${coords.y}px`,
      transform: "translateX(-50%)",
      zIndex: 9999,
      pointerEvents: "none",
      maxWidth: `${maxWidth}px`,
    };

    switch (adjustedPosition) {
      case "top":
        return { ...baseStyles, transform: "translateX(-50%) translateY(-100%)" };
      case "bottom":
        return { ...baseStyles, transform: "translateX(-50%) translateY(8px)" };
      case "left":
        return { ...baseStyles, transform: "translateX(-100%) translateY(-50%)", left: `${coords.x - 8}px`, top: `${coords.y}px` };
      case "right":
        return { ...baseStyles, transform: "translateX(0) translateY(-50%)", left: `${coords.x + 8}px`, top: `${coords.y}px` };
      default:
        return baseStyles;
    }
  };

  return (
    <>
      <span
        ref={triggerRef}
        onMouseEnter={showTooltip}
        onMouseLeave={hideTooltip}
        onFocus={showTooltip}
        onBlur={hideTooltip}
        style={{ cursor: "help", display: "inline-block" }}
      >
        {children}
      </span>

      {visible && content && (
        <div
          style={{
            ...getPositionStyles(),
            background: "var(--atlas-surface)",
            border: "1px solid var(--atlas-border)",
            borderRadius: 4,
            padding: "8px 12px",
            fontFamily: "monospace",
            fontSize: 10,
            color: "var(--atlas-text-secondary)",
            boxShadow: "0 4px 12px rgba(0, 0, 0, 0.3)",
            lineHeight: 1.5,
          }}
        >
          {content}
        </div>
      )}
    </>
  );
}

export function TooltipCell({ value, tooltip, align = "left" }) {
  return (
    <Tooltip content={tooltip} position="top">
      <span style={{ 
        textDecoration: "underline dotted var(--atlas-text-secondary)",
        textDecorationThickness: "1px",
        textUnderlineOffset: "3px"
      }}>
        {value}
      </span>
    </Tooltip>
  );
}