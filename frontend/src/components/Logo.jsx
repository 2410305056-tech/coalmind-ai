export default function Logo({ size = 36 }) {
  return (
    <svg
      className="logo"
      width={size}
      height={size}
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <rect width="64" height="64" rx="14" fill="#1B3A4B" />
      <path
        d="M20 16h18.5L46 23.5V48H20V16Z"
        fill="#F7F4EE"
      />
      <path d="M38.5 16V23.5H46" fill="#D9CDB8" />
      <path
        d="M26 31h14M26 37h14M26 43h9"
        stroke="#C4A35A"
        strokeWidth="2.6"
        strokeLinecap="round"
      />
      <path d="M24 22.5 28 19.5 32 22.5 28 25.5Z" fill="#C4A35A" />
    </svg>
  )
}
