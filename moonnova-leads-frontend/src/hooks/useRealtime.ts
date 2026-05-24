import { useEffect, useRef } from "react";
import { toast } from "sonner";
import { createRealtimeSocket, RealtimeEvent } from "@/lib/websocket";
import { useAuthStore } from "@/store/authStore";
import { useRealtimeStore } from "@/store/realtimeStore";
import type { Lead } from "@/types/lead";
import type { SearchProgressEvent } from "@/types/search";

export function useRealtime() {
  const socketRef = useRef<WebSocket | null>(null);
  const accessToken = useAuthStore((state) => state.accessToken);

  const {
    setConnected,
    setLastEvent,
    addLiveLead,
    setSearchProgress
  } = useRealtimeStore();

  useEffect(() => {
    if (!accessToken) return;

    const socket = createRealtimeSocket(accessToken);
    socketRef.current = socket;

    socket.onopen = () => {
      setConnected(true);
    };

    socket.onmessage = (message) => {
      try {
        const event: RealtimeEvent = JSON.parse(message.data);
        setLastEvent(event);

        if (event.type === "connected") {
          setConnected(true);
        }

        if (event.type === "notification" && event.message) {
          toast.info(event.message);
        }

        if (
          event.type === "search_started" ||
          event.type === "search_progress" ||
          event.type === "search_completed" ||
          event.type === "search_failed"
        ) {
          const data = event.data as SearchProgressEvent | undefined;

          const searchId =
            data?.search_id ||
            event.search_id ||
            Number((event.data as any)?.id);

          if (searchId) {
            setSearchProgress(searchId, {
              search_id: searchId,
              ...data
            });
          }

          if (event.type === "search_completed") {
            toast.success("Search completed");
          }

          if (event.type === "search_failed") {
            toast.error("Search failed");
          }
        }

        if (event.type === "lead_found") {
          const lead =
            (event.lead as Lead | undefined) ||
            ((event.data as any)?.lead as Lead | undefined) ||
            (event.data as Lead | undefined);

          if (lead?.id) {
            addLiveLead(lead);
            toast.success(`New lead found: ${lead.business_name || lead.name}`);
          }
        }
      } catch {
        console.error("Invalid WebSocket message:", message.data);
      }
    };

    socket.onerror = () => {
      setConnected(false);
    };

    socket.onclose = () => {
      setConnected(false);
    };

    return () => {
      socket.close();
      socketRef.current = null;
    };
  }, [accessToken, setConnected, setLastEvent, addLiveLead, setSearchProgress]);

}
