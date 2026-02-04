type EmptyStateProps = {
  title: string;
  description?: string;
};

export default function EmptyState({ title, description }: EmptyStateProps) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-8 text-center text-slate-300">
      <h3 className="text-base font-semibold text-slate-100">{title}</h3>
      {description ? (
        <p className="mt-2 text-sm text-slate-400">{description}</p>
      ) : null}
    </div>
  );
}
