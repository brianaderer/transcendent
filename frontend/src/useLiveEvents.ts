import { useEffect } from "react";

export type LiveEvent = { type: string; [field: string]: unknown };

/** Listens to one server-sent event stream from the backend (atlas plate 41). */
export function useLiveEvents(stream: string, onEvent: (event: LiveEvent) => void) {
  useEffect(() => {
    const source = new EventSource(`/api/streams/${stream}/events`);
    source.onmessage = (message) => onEvent(JSON.parse(message.data) as LiveEvent);
    return () => source.close();
  }, [stream, onEvent]);
}
