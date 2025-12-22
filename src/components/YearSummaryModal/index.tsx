import { lazy, Suspense, useEffect, useMemo } from 'react';
import { yearSummaryStats } from '@assets/index';
import { loadSvgComponent } from '@/utils/svgUtils';
import styles from './style.module.css';

interface YearSummaryModalProps {
  year: string;
  onClose: () => void;
}

const YearSummaryModal = ({ year, onClose }: YearSummaryModalProps) => {
  // Memoize the lazy component to prevent re-creation on each render
  const YearSummarySVG = useMemo(
    () =>
      lazy(() =>
        loadSvgComponent(yearSummaryStats, `./year_summary_${year}.svg`)
      ),
    [year]
  );

  // Close on escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  // Prevent body scroll when modal is open
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, []);

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <button className={styles.closeButton} onClick={onClose}>
          ×
        </button>
        <Suspense fallback={<div className={styles.loading}>Loading...</div>}>
          <YearSummarySVG className={styles.svg} />
        </Suspense>
      </div>
    </div>
  );
};

export default YearSummaryModal;
