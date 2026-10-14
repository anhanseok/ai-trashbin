/* eslint-disable @next/next/no-img-element -- Storage 서명 URL이라 next/image 최적화를 쓰지 않음 */

export default function Photo({ url, className = "" }: { url?: string; className?: string }) {
  if (!url) {
    return (
      <div
        className={`flex items-center justify-center rounded border border-gray-300 bg-[repeating-linear-gradient(45deg,#ddd_0_6px,#eee_6px_12px)] text-[11px] text-gray-500 ${className}`}
      >
        사진 없음
      </div>
    );
  }
  return (
    <a href={url} target="_blank" rel="noreferrer">
      <img src={url} alt="투입 사진" className={`rounded border border-gray-300 object-cover ${className}`} />
    </a>
  );
}
