export const request = async <T>(
  path: string,
  options?: RequestInit,
): Promise<T> => {
  const response = await fetch(`/api${path}`, options).catch(() => {
    throw new Error(
      "Impossibile collegarsi all’archivio locale. Controlla che Spencer sia in esecuzione.",
    );
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(
      typeof body.detail === "string"
        ? body.detail
        : "Operazione non riuscita. Riprova.",
    );
  }
  return response.json() as Promise<T>;
};

export const money = (cents: number) =>
  new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(
    cents / 100,
  );
export const dateLabel = (date: string | null) =>
  date
    ? new Intl.DateTimeFormat("it-IT", {
        day: "numeric",
        month: "short",
        year: "numeric",
      }).format(new Date(`${date}T12:00:00`))
    : "Data non disponibile";
