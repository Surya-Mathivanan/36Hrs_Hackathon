import React from 'react';
import styled, { keyframes } from 'styled-components';

const scan = keyframes`
  0%   { top: 0px; }
  25%  { top: 54px; }
  50%  { top: 0px; }
  75%  { top: 54px; }
`;

const cut = keyframes`
  0%   { clip-path: inset(0 0 0 0); }
  25%  { clip-path: inset(100% 0 0 0); }
  50%  { clip-path: inset(0 0 100% 0); }
  75%  { clip-path: inset(0 0 0 0); }
`;

const StyledWrapper = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 60px;

  .loader {
    max-width: fit-content;
    color: rgb(242, 255, 240);
    font-size: 50px;
    font-family: 'Space Grotesk', 'Outfit', sans-serif;
    position: relative;
    font-style: italic;
    font-weight: 700;
    letter-spacing: -1px;
  }

  .loader span {
    animation: ${cut} 2s infinite;
    transition: 1s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  }

  .loader:hover {
    color: #fcffdf;
  }

  .loader::after {
    position: absolute;
    content: "";
    width: 100%;
    height: 6px;
    border-radius: 4px;
    background-color: #00d4aa91;
    top: 0px;
    filter: blur(10px);
    animation: ${scan} 2s infinite;
    left: 0;
    z-index: 0;
    transition: 1s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  }

  .loader::before {
    position: absolute;
    content: "";
    width: 100%;
    height: 5px;
    border-radius: 4px;
    background-color: #00d4aa;
    top: 0px;
    animation: ${scan} 2s infinite;
    left: 0;
    z-index: 1;
    filter: opacity(0.9);
    transition: 1s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  }

  .load-text {
    color: rgba(0, 212, 170, 0.6);
    font-size: 12px;
    font-family: 'Outfit', sans-serif;
    letter-spacing: 4px;
    text-transform: uppercase;
    font-weight: 500;
  }
`;

const Loader = ({ label = 'Loading' }) => {
  return (
    <StyledWrapper>
      <p className="loader"><span>{label}</span></p>
      <span className="load-text">Please wait...</span>
    </StyledWrapper>
  );
};

export default Loader;
