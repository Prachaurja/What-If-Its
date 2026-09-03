import { useQuery } from "@tanstack/react-query";
import { getCheck } from "../api/checks";

// Polls a check every 2s until it's done or failed.
export function useCheck(id: number | null) {
  return useQuery({
    queryKey: ["check", id],
    queryFn: () => getCheck(id!),
    enabled: id != null,
    refetchInterval: (q) => {
      const s = q.state.data?.status;
      return s === "done" || s === "failed" ? false : 2000;
    },
  });
}
