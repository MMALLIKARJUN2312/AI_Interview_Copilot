export interface UserResponse {
  id: number;
  full_name: string;
  email: string;
  role: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface ResumeSummary {
  id: number;
  original_filename: string;
  target_role: string;
  status: "uploaded" | "analyzed" | "failed";
  created_at: string;
}

export interface ResumeAnalysisResponse {
  resume_id: number;
  analysis_id: number;
  target_role: string;
  ats_score: number;
  strengths: string[];
  weaknesses: string[];
  suggestions: string[];
}

export type InterviewSessionStatus =
  | "pending"
  | "in_progress"
  | "completed"
  | "abandoned";

export interface SessionSummary {
  id: number;
  resume_id: number;
  target_role: string;
  status: InterviewSessionStatus;
  total_questions: number;
  current_index: number;
  overall_score: number | null;
  created_at: string;
  completed_at: string | null;
}

export type RoundType = "dsa_coding" | "machine_coding" | "general";

export type CodeLanguage = "python" | "javascript" | "java" | "cpp";

export interface TestCase {
  input: string;
  expected_output: string;
}

export interface QuestionResponse {
  id: number;
  order_index: number;
  question_text: string;
  category: string;
  difficulty: string;
  round_type: RoundType;
  language: string | null;
  starter_code: string | null;
  examples: string | null;
  constraints: string | null;
  test_cases: TestCase[];
}

export interface ExecutionResult {
  input: string;
  expected_output: string;
  actual_output: string;
  passed: boolean;
  stderr: string;
}

export interface AnswerResponse {
  id: number;
  question_id: number;
  score: number;
  feedback: string;
  strengths: string[];
  improvements: string[];
  language: string | null;
  passed_test_count: number | null;
  total_test_count: number | null;
  execution_results: ExecutionResult[] | null;
}

export interface RoundConfig {
  round_type: RoundType;
  num_questions: number;
}

export interface RunCodeResponse {
  results: ExecutionResult[];
  all_passed: boolean;
}

export interface QuestionWithAnswer extends QuestionResponse {
  answer: AnswerResponse | null;
}

export interface StartInterviewResponse {
  session: SessionSummary;
  first_question: QuestionResponse | null;
}

export interface SubmitAnswerResponse {
  answer: AnswerResponse;
  next_question: QuestionResponse | null;
  is_complete: boolean;
}

export interface FeedbackResponse {
  overall_score: number;
  summary: string;
  strengths: string[];
  weaknesses: string[];
  recommendation: string;
}

export interface RoadmapItem {
  topic: string;
  description: string;
  priority: string;
  resources: string[];
}

export interface RoadmapResponse {
  items: RoadmapItem[];
}

export interface CompleteInterviewResponse {
  session: SessionSummary;
  feedback: FeedbackResponse;
  roadmap: RoadmapResponse;
}

export interface SessionDetailResponse {
  session: SessionSummary;
  questions: QuestionWithAnswer[];
  feedback: FeedbackResponse | null;
  roadmap: RoadmapResponse | null;
}
