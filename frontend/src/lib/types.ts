export type ApiResponse<T> = {
  success: boolean;
  data: T | null;
  error: { code: string; message: string; field?: string } | null;
  meta: { request_id: string; timestamp: string; version: string };
};

export type Option = { label: string; value: string };

export type Question = {
  id: string;
  category: string;
  question_text: string;
  description: string | null;
  input_type: "range_slider" | "checkbox" | "radio" | "dropdown" | "text_input";
  options: Option[] | null;
  range: { min: number; max: number; step: number; unit: string } | null;
  default_value: any;
  placeholder: string | null;
  is_required: boolean;
  depends_on: { question_id: string; value: any } | null;
  validation: any;
  priority: number;
  mode: string;
  tags: string[];
};

export type Product = {
  id: string;
  name: string;
  image: string | null;
  description: string;
  features: string[];
  match_score: number;
  match_reasons: string[];
  missing_features: string[] | null;
  review_summary: {
    rating: number;
    sentiment: string;
    highlights: string[];
    concerns: string[];
  };
  reliability: { score: number; summary: string };
  warranty: { duration: string; type: string };
};

export type Price = {
  marketplace: string;
  price: number;
  currency: string;
  url: string;
  availability: "in_stock" | "limited" | "out_of_stock";
  is_best: boolean;
};
