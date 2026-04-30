export type ArticleEntityResponse = {
  id: string;
  entity_type: string;
  name: string;
  symbol: string | null;
  canonical_name: string;
  relationship_type: string;
  confidence_score: string;
  evidence_snippets: string[];
  provider: string;
  model_name: string;
  model_version: string;
};

export type ArticleResponse = {
  id: string;
  title: string | null;
  source: string | null;
  url: string | null;
  input_type: string;
  content_hash: string;
  word_count: number;
  raw_artifact_path: string | null;
  relevance_score: string | null;
  duplicate_group_id: string | null;
  included_in_forecast: boolean;
  exclusion_reason: string | null;
  entities: ArticleEntityResponse[];
};

export type TrackingNeedResponse = {
  id: string;
  entity_id: string;
  entity_type: string;
  name: string;
  symbol: string | null;
  canonical_name: string;
  suggested_symbol: string | null;
  tracking_type: string;
  reason: string;
  evidence_snippets: string[];
  priority_score: string;
  status: string;
  provider: string;
  model_name: string;
  model_version: string;
};

export type MarketQuoteResponse = {
  provider: string;
  price: string | null;
  previous_close: string | null;
  volume: number | null;
  market_cap: number | null;
  quote_time: string | null;
  retrieved_at: string;
};

export type SentimentAggregateResponse = {
  article_count: number;
  included_article_count: number;
  positive_count: number;
  neutral_count: number;
  negative_count: number;
  aggregate_score: string | null;
  agreement_score: string | null;
  evidence_strength_score: string | null;
  summary: string | null;
};

export type ForecastRunResponse = {
  id: string;
  horizon: string;
  provider: string;
  model_name: string;
  model_version: string;
  predicted_direction: string;
  predicted_percent_change: string | null;
  confidence_score: string;
  baseline_direction: string | null;
  baseline_percent_change: string | null;
  top_factors: string[];
  limitations: string[];
  target_start_price: string | null;
  target_end_time: string | null;
};

export type AnalysisResponse = {
  id: string;
  ticker: string;
  status: string;
  primary_horizon: string;
  input_mode: string;
  created_at: string;
  completed_at: string | null;
  error_message: string | null;
  message: string;
  limitations: string[];
  articles: ArticleResponse[];
  market_quote: MarketQuoteResponse | null;
  sentiment_aggregate: SentimentAggregateResponse | null;
  forecast_runs: ForecastRunResponse[];
  tracking_needs: TrackingNeedResponse[];
};

export type EvaluationHorizonSummary = {
  horizon: string;
  evaluated_forecasts: number;
  directional_accuracy: string | null;
  mean_absolute_error: string | null;
  baseline_mean_absolute_error: string | null;
};

export type EvaluationSummaryResponse = {
  evaluated_forecasts: number;
  by_horizon: EvaluationHorizonSummary[];
};

export type EvaluationRefreshResponse = {
  status: string;
  evaluated_forecasts: number;
  skipped_forecasts: number;
  errors: { forecast_run_id: string; message: string }[];
};

export type ArticleHistoryItem = {
  article: ArticleResponse;
  analyses: string[];
};
