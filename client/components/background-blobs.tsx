export function BackgroundBlobs() {
  return (
    <div
      aria-hidden
      className="pointer-events-none fixed inset-0 -z-10 overflow-hidden"
    >
      <div
        className="animate-blob absolute -top-40 -left-32 h-[36rem] w-[36rem] rounded-full opacity-60 blur-3xl"
        style={{
          background:
            "radial-gradient(circle at center, var(--brand-from), transparent 72%)",
        }}
      />
      <div
        className="animate-blob absolute top-1/3 -right-44 h-[32rem] w-[32rem] rounded-full opacity-50 blur-3xl"
        style={{
          background:
            "radial-gradient(circle at center, var(--brand-to), transparent 72%)",
          animationDelay: "-6s",
        }}
      />
      <div
        className="animate-blob absolute -bottom-36 left-1/4 h-[30rem] w-[30rem] rounded-full opacity-45 blur-3xl"
        style={{
          background:
            "radial-gradient(circle at center, var(--brand-via), transparent 72%)",
          animationDelay: "-11s",
        }}
      />
    </div>
  );
}
