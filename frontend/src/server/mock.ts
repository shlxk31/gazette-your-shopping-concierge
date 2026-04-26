// Server-side mock data + helpers. Used by /api/* server routes.
// All shapes mirror the spec's JSON examples exactly.

export function wrap<T>(data: T) {
  return {
    success: true,
    data,
    error: null,
    meta: {
      request_id: "req_" + Math.random().toString(36).slice(2, 10),
      timestamp: new Date().toISOString(),
      version: "v1",
    },
  };
}

export function fail(code: string, message: string, field?: string) {
  return {
    success: false,
    data: null,
    error: { code, message, field },
    meta: {
      request_id: "req_" + Math.random().toString(36).slice(2, 10),
      timestamp: new Date().toISOString(),
      version: "v1",
    },
  };
}

export function detectCategory(query: string): string {
  const q = query.toLowerCase();
  if (/laptop|macbook|computer/.test(q)) return "laptop";
  if (/chair|desk|ergonomic|office/.test(q)) return "office_furniture";
  if (/earbud|headphone|earphone|airpod/.test(q)) return "audio";
  if (/phone|iphone|android/.test(q)) return "smartphone";
  return "general";
}

export function initialQuestionsFor(category: string) {
  // Default budget unit by category
  const isINR = category === "laptop" || category === "smartphone";
  const unit = isINR ? "INR" : "USD";
  const range = isINR
    ? { min: 30000, max: 300000, step: 5000, unit }
    : { min: 50, max: 5000, step: 50, unit };
  const defaultBudget = isINR ? 80000 : 500;

  // Category-specific use_case question
  let useCase: any;
  if (category === "laptop") {
    useCase = {
      id: "use_case",
      category: "usage",
      question_text: "What programming do you do?",
      description: "Select all that apply.",
      input_type: "checkbox",
      options: [
        { label: "Machine Learning", value: "ml" },
        { label: "Web Development", value: "web_dev" },
        { label: "Data Science", value: "data_science" },
        { label: "Mobile Apps", value: "mobile" },
        { label: "Game Dev", value: "game_dev" },
        { label: "DevOps / Cloud", value: "devops" },
      ],
      range: null,
      default_value: null,
      placeholder: null,
      is_required: true,
      depends_on: null,
      validation: null,
      priority: 2,
      mode: "basic",
      tags: ["usage", "performance"],
    };
  } else if (category === "office_furniture") {
    useCase = {
      id: "use_case",
      category: "usage",
      question_text: "How will you use this?",
      description: "Select all that apply.",
      input_type: "checkbox",
      options: [
        { label: "Long work sessions", value: "long_sessions" },
        { label: "Back pain support", value: "back_pain" },
        { label: "Gaming", value: "gaming" },
        { label: "Casual use", value: "casual" },
      ],
      range: null,
      default_value: null,
      placeholder: null,
      is_required: true,
      depends_on: null,
      validation: null,
      priority: 2,
      mode: "basic",
      tags: ["usage"],
    };
  } else if (category === "audio") {
    useCase = {
      id: "use_case",
      category: "usage",
      question_text: "Where will you use these most?",
      description: "Select all that apply.",
      input_type: "checkbox",
      options: [
        { label: "Gym / Workouts", value: "gym" },
        { label: "Commute", value: "commute" },
        { label: "Office", value: "office" },
        { label: "Travel", value: "travel" },
      ],
      range: null,
      default_value: null,
      placeholder: null,
      is_required: true,
      depends_on: null,
      validation: null,
      priority: 2,
      mode: "basic",
      tags: ["usage"],
    };
  } else {
    useCase = {
      id: "use_case",
      category: "usage",
      question_text: "What will you use this for?",
      description: "Select all that apply.",
      input_type: "checkbox",
      options: [
        { label: "Personal", value: "personal" },
        { label: "Professional", value: "professional" },
        { label: "Gift", value: "gift" },
      ],
      range: null,
      default_value: null,
      placeholder: null,
      is_required: true,
      depends_on: null,
      validation: null,
      priority: 2,
      mode: "basic",
      tags: ["usage"],
    };
  }

  return [
    {
      id: "budget",
      category: "budget",
      question_text: "What is your budget?",
      description: "We'll find the best options within your range.",
      input_type: "range_slider",
      options: null,
      range,
      default_value: defaultBudget,
      placeholder: null,
      is_required: true,
      depends_on: null,
      validation: { min: range.min, max: range.max, regex: null },
      priority: 1,
      mode: "basic",
      tags: ["budget"],
    },
    useCase,
    {
      id: "preference_strength",
      category: "preference",
      question_text: "Any brand preference?",
      description: null,
      input_type: "dropdown",
      options: [
        { label: "No preference", value: "any" },
        { label: "Premium brands only", value: "premium" },
        { label: "Best value", value: "value" },
      ],
      range: null,
      default_value: "any",
      placeholder: "Select a preference...",
      is_required: false,
      depends_on: null,
      validation: null,
      priority: 5,
      mode: "basic",
      tags: ["brand"],
    },
  ];
}

export function nextQuestionsFor(category: string) {
  if (category === "laptop") {
    return [
      {
        id: "portability",
        category: "preference",
        question_text: "How important is portability?",
        description: "Affects weight and battery life recommendations.",
        input_type: "radio",
        options: [
          { label: "Very important", value: "high" },
          { label: "Somewhat", value: "medium" },
          { label: "Not at all", value: "low" },
        ],
        range: null,
        default_value: null,
        placeholder: null,
        is_required: true,
        depends_on: null,
        validation: null,
        priority: 1,
        mode: "basic",
        tags: ["preference"],
      },
      {
        id: "extra_notes",
        category: "preference",
        question_text: "Anything else we should know?",
        description: "Optional — share any specific requirement.",
        input_type: "text_input",
        options: null,
        range: null,
        default_value: null,
        placeholder: "e.g. needs USB-C only, prefer matte screen...",
        is_required: false,
        depends_on: null,
        validation: null,
        priority: 2,
        mode: "basic",
        tags: ["preference"],
      },
    ];
  }
  return [
    {
      id: "priority_factor",
      category: "preference",
      question_text: "What matters most to you?",
      description: null,
      input_type: "radio",
      options: [
        { label: "Quality", value: "quality" },
        { label: "Price", value: "price" },
        { label: "Brand", value: "brand" },
      ],
      range: null,
      default_value: null,
      placeholder: null,
      is_required: true,
      depends_on: null,
      validation: null,
      priority: 1,
      mode: "basic",
      tags: ["preference"],
    },
  ];
}

export function productsFor(category: string) {
  if (category === "office_furniture") {
    return [
      {
        id: "prod_branch_chair",
        name: "Branch Ergonomic Chair",
        image: "https://images.unsplash.com/photo-1592078615290-033ee584e267?w=800",
        description: "Award-winning ergonomic chair built for long workdays.",
        features: ["Lumbar Support", "Breathable Mesh", "7-way Adjustable"],
        match_score: 98,
        match_reasons: [
          "Exceptional lower back support for long sessions",
          "Premium build quality at mid-range price",
          "Highly recommended on r/Ergonomics",
        ],
        missing_features: ["Headrest must be purchased separately"],
        review_summary: {
          rating: 4.7,
          sentiment: "positive",
          highlights: ["Highly recommended on r/Ergonomics"],
          concerns: ["Headrest sold separately"],
        },
        reliability: { score: 9, summary: "Very reliable" },
        warranty: { duration: "7 years", type: "manufacturer" },
      },
      {
        id: "prod_steelcase_s1",
        name: "Steelcase Series 1",
        image: "https://images.unsplash.com/photo-1505843490578-27c5b6b8a5b9?w=800",
        description: "Compact ergonomic chair with weight-activated mechanism.",
        features: ["Compact Design", "Weight-activated Mech"],
        match_score: 85,
        match_reasons: [
          "Incredible build quality and 12-year warranty",
          "Great for smaller spaces",
        ],
        missing_features: ["Seat pan might be too shallow for taller users"],
        review_summary: {
          rating: 4.5,
          sentiment: "positive",
          highlights: ["Top rated by 'Tech Setup' YouTubers"],
          concerns: ["Shallow seat pan for tall users"],
        },
        reliability: { score: 9, summary: "Industry leader" },
        warranty: { duration: "12 years", type: "manufacturer" },
      },
    ];
  }
  if (category === "laptop") {
    return [
      {
        id: "prod_mbp_m3",
        name: "MacBook Pro M3",
        image: "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=800",
        description: "Apple's most powerful laptop, built for creators and developers.",
        features: ["M3 Pro Chip", "18GB RAM", "512GB SSD", "18hr Battery"],
        match_score: 96,
        match_reasons: [
          "Exceptional ML performance via Neural Engine",
          "macOS matches your OS preference",
          "18-hour battery for on-the-go work",
        ],
        missing_features: ["No dedicated NVIDIA GPU for CUDA workflows"],
        review_summary: {
          rating: 4.8,
          sentiment: "positive",
          highlights: ["Highly recommended on r/MachineLearning"],
          concerns: ["Expensive vs Windows alternatives"],
        },
        reliability: { score: 9, summary: "Highly reliable" },
        warranty: { duration: "1 year", type: "manufacturer" },
      },
      {
        id: "prod_dell_xps15",
        name: "Dell XPS 15",
        image: "https://images.unsplash.com/photo-1593642632559-0c6d3fc62b89?w=800",
        description: "Premium Windows laptop with OLED display and dedicated GPU.",
        features: ["Intel i9", "32GB RAM", "RTX 4060", "OLED Display"],
        match_score: 87,
        match_reasons: [
          "Dedicated NVIDIA GPU for CUDA and ML training",
          "High RAM suits data science workloads",
        ],
        missing_features: [
          "Heavier at 1.86kg, less portable",
          "Battery life shorter than MacBook",
        ],
        review_summary: {
          rating: 4.3,
          sentiment: "positive",
          highlights: ["Top rated on r/SuggestALaptop for developers"],
          concerns: ["Runs hot under sustained load"],
        },
        reliability: { score: 7, summary: "Generally reliable" },
        warranty: { duration: "1 year", type: "manufacturer" },
      },
    ];
  }
  if (category === "audio") {
    return [
      {
        id: "prod_jabra_85t",
        name: "Jabra Elite 8 Active",
        image: "https://images.unsplash.com/photo-1606220588913-b3aacb4d2f46?w=800",
        description: "Most rugged earbuds for workouts with military-grade durability.",
        features: ["IP68", "8hr Battery", "ANC", "Secure Fit"],
        match_score: 94,
        match_reasons: [
          "Best secure fit for high-intensity gym workouts",
          "Sweat and shock proof rated MIL-STD-810H",
          "Top pick by The Verge for fitness",
        ],
        missing_features: ["Audio quality below premium tier"],
        review_summary: {
          rating: 4.6,
          sentiment: "positive",
          highlights: ["Top pick for fitness on r/headphones"],
          concerns: ["Case is bulky"],
        },
        reliability: { score: 9, summary: "Very durable" },
        warranty: { duration: "2 years", type: "manufacturer" },
      },
      {
        id: "prod_powerbeats_pro",
        name: "Powerbeats Pro 2",
        image: "https://images.unsplash.com/photo-1572569511254-d8f925fe2cbb?w=800",
        description: "Apple's fitness-tuned earbuds with ear hooks for total stability.",
        features: ["Ear Hooks", "10hr Battery", "Heart Rate", "ANC"],
        match_score: 89,
        match_reasons: [
          "Ear hooks guarantee they stay in during burpees",
          "Heart rate sensor built in",
        ],
        missing_features: ["Premium price", "Larger than typical earbuds"],
        review_summary: {
          rating: 4.5,
          sentiment: "positive",
          highlights: ["Highly recommended on r/Fitness"],
          concerns: ["Pricey"],
        },
        reliability: { score: 8, summary: "Solid build" },
        warranty: { duration: "1 year", type: "manufacturer" },
      },
    ];
  }
  return [
    {
      id: "prod_generic",
      name: "Top Recommendation",
      image: null,
      description: "Best match for your search.",
      features: ["Premium build", "Top rated", "Best value"],
      match_score: 90,
      match_reasons: ["Matches your stated preferences", "Highly reviewed"],
      missing_features: null,
      review_summary: {
        rating: 4.5,
        sentiment: "positive",
        highlights: ["Top rated across review sites"],
        concerns: [],
      },
      reliability: { score: 8, summary: "Reliable" },
      warranty: { duration: "1 year", type: "manufacturer" },
    },
  ];
}

export function pricesFor(productId: string) {
  // category-aware-ish; just return varied marketplaces
  const isINR = productId.includes("mbp") || productId.includes("xps");
  const currency = isINR ? "INR" : "USD";
  const base = isINR ? 189900 : 329;
  const data = isINR
    ? [
        { marketplace: "Amazon", price: base, delta: 0, avail: "in_stock", best: true },
        { marketplace: "Flipkart", price: base + 3099, delta: 0, avail: "in_stock", best: false },
        { marketplace: "Croma", price: base + 5100, delta: 0, avail: "limited", best: false },
        { marketplace: "Apple Store", price: base + 10000, delta: 0, avail: "in_stock", best: false },
      ]
    : productId.includes("steelcase")
    ? [
        { marketplace: "Amazon", price: 493, avail: "in_stock", best: true, delta: 0 },
        { marketplace: "Steelcase", price: 510, avail: "in_stock", best: false, delta: 0 },
      ]
    : productId.includes("branch")
    ? [
        { marketplace: "Branch", price: 329, avail: "in_stock", best: true, delta: 0 },
        { marketplace: "Amazon", price: 339, avail: "in_stock", best: false, delta: 0 },
        { marketplace: "Wayfair", price: 349, avail: "limited", best: false, delta: 0 },
      ]
    : [
        { marketplace: "Amazon", price: base - 10, avail: "in_stock", best: true, delta: 0 },
        { marketplace: "Best Buy", price: base, avail: "in_stock", best: false, delta: 0 },
        { marketplace: "Target", price: base + 15, avail: "limited", best: false, delta: 0 },
      ];
  return data.map((d) => ({
    marketplace: d.marketplace,
    price: d.price,
    currency,
    url: "https://example.com/" + d.marketplace.toLowerCase().replace(/\s+/g, "-"),
    availability: d.avail as "in_stock" | "limited" | "out_of_stock",
    is_best: d.best,
  }));
}
