// @soccer-forge/shared — contratos mínimos (Fase 0, por cerrar en detalle).
// Tiempo en segundos, siempre en tiempo de archivo salvo que se indique
// explícitamente que es reloj de partido.

export type EventType = "pass" | "carry" | "recovery" | "loss" | "shot";
export type EventResult =
  | "completed"
  | "intercepted"
  | "out"
  | "goal"
  | "saved"
  | "blocked"
  | "ongoing";

export interface MatchEvent {
  id: string;
  matchId: string;
  type: EventType;
  tStart: number;
  tEnd: number;
  teamId?: string;
  playerIds: string[];
  result?: EventResult;
  confidence: number; // 0..1
  evidenceClipId: string;
  status: "auto" | "reviewed" | "corrected" | "pending";
}

export interface Play {
  id: string;
  matchId: string;
  tStart: number;
  tEnd: number;
  events: MatchEvent[];
  participants: string[];
  interpretation?: string;
  quality: { coverage: number; uncertainty: string };
  evidenceClipId: string;
  reviewStatus: "auto" | "reviewed" | "corrected" | "pending";
}

export type JobStage =
  | "reception"
  | "preparation"
  | "segmentation"
  | "perception"
  | "tracking"
  | "calibration"
  | "events"
  | "muse-review"
  | "validation"
  | "publication";

export interface AnalysisJob {
  id: string;
  matchId: string;
  stage: JobStage;
  stageStatus: "pending" | "running" | "done" | "failed";
  progress: number; // 0..100
  error?: string;
}
