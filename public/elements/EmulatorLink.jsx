import React from 'react';
import { Button } from '@/components/ui/button';
import { useContext } from 'react';

const EmulatorLinkButtonElement = () => {
  const handleClick = () => {
    popupLoaded = false;
    if (Object.hasOwn(window, 'emulator_popup')) {
      if (window.emulator_popup && !window.emulator_popup.closed) {
        window.emulator_popup.focus();
        popupLoaded = true;
      } else {
        window.emulator_popup = window.open(props.target_origin, 'c64_emulator', 'width=1024,height=768');
      }
    } else {
      window.emulator_popup = window.open(props.target_origin, 'c64_emulator', 'width=1024,height=768');
    }
    if (!window.emulator_popup) {
      console.warn('Popup blocked or failed to open.');
      return;
    }

    // Decode the base64 string back to a binary array
    const prgString = atob(props.prg_binary_base64);
    const prgBinaryArray = new Uint8Array(prgString.length);
    for (let i = 0; i < prgString.length; i++) {
        prgBinaryArray[i] = prgString.charCodeAt(i);
    }
    
    const messageArray = prgBinaryArray;

    if (popupLoaded) {
      window.emulator_popup.postMessage(messageArray, "*");
    } else {
      setTimeout(() => {
        window.emulator_popup.postMessage(messageArray, "*");
      }, 4000);
    }
  };

  return (
    <Button  
      onClick={handleClick}
      className="w" variant="default"
      size="sm"
    > {props.button_label}
    </Button>
  );
};

export default EmulatorLinkButtonElement;
