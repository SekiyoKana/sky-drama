import { driver, type DriveStep } from "driver.js";
import "driver.js/dist/driver.css";
import { userApi } from "@/api";
import { i18n } from "@/i18n";

export interface TourStep {
  element: string;
  theme?: 'yellow' | 'pink' | 'blue' | 'green' | 'purple';
  image?: string;
  popover: {
    title: string;
    description: string;
    side?: "top" | "right" | "bottom" | "left";
    align?: "start" | "center" | "end";
  };
}

const injectTourStyles = () => {
  if (document.getElementById('sky-drama-tour-styles')) return;
  
  const style = document.createElement('style');
  style.id = 'sky-drama-tour-styles';
  style.textContent = `
    /* Overlay - Deep blackboard feel */
    .driver-overlay path {
      fill: rgba(30, 35, 40, 0.9) !important;
    }
    
    /* Popover Container - Post-it Note Style */
    .driver-popover {
      /* Default theme (Yellow) fallback */
      background-color: #fef08a !important; 
      color: #4a4a4a !important;
      border: none !important;
      border-radius: 12px !important; /* Rounded corners */
      box-shadow: 
        0 10px 15px -3px rgba(0, 0, 0, 0.1), 
        0 4px 6px -2px rgba(0, 0, 0, 0.05),
        2px 2px 5px rgba(0,0,0,0.2) !important;
      transform: rotate(-1deg);
      font-family: 'Comic Sans MS', 'Chalkboard SE', sans-serif !important;
      padding: 20px !important;
      max-width: 320px !important;
      min-width: 250px !important;
      overflow: visible !important; /* Allow sticker to overflow */
    }

    /* THEMES - Flat Colors (No Gradients) */
    .driver-popover.theme-yellow { background-color: #fef08a !important; }
    .driver-popover.theme-pink   { background-color: #fbcfe8 !important; }
    .driver-popover.theme-blue   { background-color: #bae6fd !important; }
    .driver-popover.theme-green  { background-color: #bbf7d0 !important; }
    .driver-popover.theme-purple { background-color: #e9d5ff !important; }

    /* Tape effect on top */
    .driver-popover::before {
      content: '';
      position: absolute;
      top: -10px;
      left: 50%;
      transform: translateX(-50%) rotate(2deg);
      width: 80px;
      height: 25px;
      background-color: rgba(255, 255, 255, 0.4);
      border: 1px solid rgba(255,255,255,0.2);
      box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    
    /* REMOVE Default Arrow (Little Tail) */
    .driver-popover-arrow {
      display: none !important;
    }

    .driver-popover-image {
      position: absolute;
      top: -140px;
      right: -80px;
      bottom: auto; 
      width: 160px;
      height: 160px;
      object-fit: contain;
      z-index: 20; 
      border: none !important;
      border-radius: 0 !important;
      filter: drop-shadow(2px 4px 6px rgba(0,0,0,0.2));
      opacity: 1; 
      transform: rotate(15deg);
      pointer-events: none;
      background: transparent !important;
    }
    
    .driver-popover-description, .driver-popover-title, .driver-popover-footer {
        position: relative;
        z-index: 1; 
    }

    /* Title */
    .driver-popover-title {
      font-size: 18px !important;
      font-weight: bold !important;
      color: #1f2937 !important;
      margin-bottom: 8px !important;
      font-family: inherit !important;
    }

    /* Description */
    .driver-popover-description {
      font-size: 14px !important;
      line-height: 1.5 !important;
      color: #374151 !important;
      font-family: inherit !important;
    }

    /* Buttons - Hand-drawn box style */
    .driver-popover-footer button {
      background-color: transparent !important;
      border: 2px solid #4b5563 !important;
      color: #4b5563 !important;
      border-radius: 255px 15px 225px 15px / 15px 225px 15px 255px !important;
      padding: 5px 12px !important;
      font-weight: bold !important;
      text-shadow: none !important;
      transition: all 0.2s !important;
      font-family: inherit !important;
    }

    .driver-popover-footer button:hover {
      background-color: #4b5563 !important;
      color: #fef08a !important; /* Yellow text on hover default */
      transform: scale(1.05) rotate(1deg);
    }

    .driver-popover-navigation-btns {
      gap: 8px !important;
    }

    .driver-popover-close-btn {
      color: #6b7280 !important;
    }
    
    /* Comic Arrow (SVG Background) */
    /* We insert this via JS per step or global after pseudo element */
    /* Bright white/yellow arrow to contrast with dark overlay */
    .driver-popover::after {
      display: none !important;
    }
    
    /* Dynamic Arrow Positioning logic is hard in CSS alone without knowing "side" */
    /* Overriding default arrow with specific classes provided by driver.js if available */
    /* Driver.js adds classes like driver-popover-arrow-side-left */
    
    .driver-popover-arrow-side-left { display: none !important; }
    .driver-popover-arrow-side-right { display: none !important; }
    .driver-popover-arrow-side-top { display: none !important; }
    .driver-popover-arrow-side-bottom { display: none !important; }
  `;
  document.head.appendChild(style);
};

export const startOnboardingTour = async (tourId: string, steps: TourStep[]) => {
  try {
    injectTourStyles();
    
    const storageKey = `tour_completed_${tourId}`;
    if (localStorage.getItem(storageKey)) {
        return;
    }

    await userApi.getMe();

    const driverSteps: DriveStep[] = steps.map(step => {
      let descriptionHtml = step.popover.description;
      
      if (step.image) {
        descriptionHtml = `
            <img src="${step.image}" class="driver-popover-image" alt="Sticker" />
            <div style="position: relative; z-index: 1;">${descriptionHtml}</div>
        `;
      }

      const side = step.popover.side || 'bottom';
      
      const arrowClass = `has-arrow-${side}`;

      return {
        element: step.element,
        popover: {
          title: step.popover.title,
          description: descriptionHtml,
          side: step.popover.side,
          align: step.popover.align,
          popoverClass: `driver-popover theme-${step.theme || 'yellow'} ${arrowClass}` 
        }
      };
    });
    
    // Inject Dynamic Arrow CSS
    const arrowStyleId = 'sky-drama-tour-arrows';
    if (!document.getElementById(arrowStyleId)) {
        const arrowStyle = document.createElement('style');
        arrowStyle.id = arrowStyleId;
        
        arrowStyle.textContent = `
            .driver-popover::after {
                display: none !important;
            }
        `;
        document.head.appendChild(arrowStyle);
    }
    
    const tourDriver = driver({
      showProgress: true,
      allowClose: false, 
      animate: true,
      overlayColor: 'rgba(30, 35, 40, 0.9)',
      steps: driverSteps,
      nextBtnText: String(i18n.global.t('tour.next')),
      prevBtnText: String(i18n.global.t('tour.prev')),
      doneBtnText: String(i18n.global.t('tour.done')),
      
      onDestroyed: () => {
        localStorage.setItem(storageKey, 'true');
        if (tourId === 'main_onboarding') {
            markOnboardingComplete();
        }
      }
    });

    tourDriver.drive();

  } catch (e) {
    console.error("Error starting onboarding tour:", e);
  }
};

const markOnboardingComplete = async () => {
  try {
    await userApi.completeOnboarding();
  } catch (e) {
    console.error("Failed to update onboarding status", e);
  }
};
