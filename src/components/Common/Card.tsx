import { ReactNode, CSSProperties } from 'react';
import './Card.css';

interface CardProps {
  title?: string;
  children: ReactNode;
  className?: string;
  style?: CSSProperties;
  headerAction?: ReactNode;
}

export function Card({ title, children, className = '', style, headerAction }: CardProps) {
  return (
    <div className={`card ${className}`} style={style}>
      {title && (
        <div className="card-header">
          <h3 className="card-title">{title}</h3>
          {headerAction && <div className="card-header-action">{headerAction}</div>}
        </div>
      )}
      <div className="card-body">{children}</div>
    </div>
  );
}
