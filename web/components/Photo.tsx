/* eslint-disable @next/next/no-img-element -- Storage 서명 URL이라 next/image 최적화를 쓰지 않음 */

export default function Photo({ url, className = "" }: { url?: string; className?: string }) {
  if (!url) {
    return (
      <div
        className={`flex items-center justify-center rounded border border-line bg-[repeating-linear-gradient(45deg,#172230_0_6px,#111922_6px_12px)] text-[11px] text-dim ${className}`}
      >
        사진 없음
      </div>
    );
  }
  return (
    <a href={url} target="_blank" rel="noreferrer">
      <img src={url} alt="투입 사진" className={`rounded border border-line object-cover ${className}`} />
    </a>
  );
}
