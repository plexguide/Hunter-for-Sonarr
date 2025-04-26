import React from 'react';



function onModalClose() {
  // No-op
}

interface AuthenticationRequiredModalProps {
  isOpen: boolean;
}

export default function AuthenticationRequiredModal({

}: AuthenticationRequiredModalProps) {
  return (
    <>
    <div onModalClose={onModalClose}>
      </div>
    </>
  );
}