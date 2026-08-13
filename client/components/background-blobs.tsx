export function BackgroundBlobs() {
  return (
    <div
      aria-hidden
      className="pointer-events-none fixed inset-0 -z-10 overflow-hidden"
    >
      <div
        className="animate-blob absolute -top-40 -left-32 h-[32rem] w-[32rem] rounded-full opacity-40 blur-3xl"
        style={{
          background:
            "radial-gradient(circle at center, var(--brand-from), transparent 70%)",
        }}
      />
      <div
        className="animate-blob absolute top-1/3 -right-40 h-[28rem] w-[28rem] rounded-full opacity-30 blur-3xl"
        style={{
          background:
            "radial-gradient(circle at center, var(--brand-to), transparent 70%)",
          animationDelay: "-6s",
        }}
      />
      <div
        className="animate-blob absolute -bottom-32 left-1/4 h-[26rem] w-[26rem] rounded-full opacity-25 blur-3xl"
        style={{
          background:
            "radial-gradient(circle at center, var(--brand-via), transparent 70%)",
          animationDelay: "-11s",
        }}
      />
    </div>
  );
}
