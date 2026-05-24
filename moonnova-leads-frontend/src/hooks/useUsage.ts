import { useQuery } from "@tanstack/react-query";
import { usageService } from "@/services/usage.service";
import { useAuthStore } from "@/store/authStore";

export function useUsage() {
  const accessToken = useAuthStore((state) => state.accessToken);

  return useQuery({
    queryKey: ["usage", "me"],
    queryFn: usageService.getMyUsage,
    enabled: Boolean(accessToken),
    refetchInterval: 30000
  });
}
