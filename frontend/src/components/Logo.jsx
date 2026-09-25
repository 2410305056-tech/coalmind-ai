export default function Logo({ size = 40 }) {
  return (
    <svg
      className="logo"
      width={size}
      height={size}
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label="CoalMind AI"
    >
      <rect width="64" height="64" rx="16" fill="#1B3A4B" />
      <rect x="2.5" y="2.5" width="59" height="59" rx="14" stroke="#C4A35A" strokeOpacity="0.45" />
      {/* Geological C — archive / CMPDI report */}
      <path
        d="M46 17.5C36.2 17.5 18 22.2 18 32.5C18 42.8 36.2 47.5 46 47.5"
        stroke="#F7F4EE"
        strokeWidth="7.2"
        strokeLinecap="round"
      />
      <path
        d="M44.5 22C37 22 24.5 25.4 24.5 32.5C24.5 39.6 37 43 44.5 43"
        stroke="#C4A35A"
        strokeWidth="2.2"
        strokeLinecap="round"
      />
      {/* Coal crystal */}
      <path
        d="M47 24.2 55.2 29v10.6L47 44.8 38.8 39.6V29Z"
        fill="#C4A35A"
      />
      <path d="M47 24.2 55.2 29 47 33.6 38.8 29Z" fill="#E8D7A8" />
      <path d="M47 33.6 55.2 29v10.6L47 44.8Z" fill="#A6863E" />
      {/* AI spark */}
      <path
        d="M50.2 12.5 51.4 15.6 54.5 16.8 51.4 18 50.2 21.1 49 18 45.9 16.8 49 15.6Z"
        fill="#F7F4EE"
      />
    </svg>
  )
}
