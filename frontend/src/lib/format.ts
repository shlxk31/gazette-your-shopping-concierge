export function formatPrice(amount: number, currency: string): string {
  if (currency === "INR") {
    return "₹" + amount.toLocaleString("en-IN");
  }
  if (currency === "USD") {
    return "$" + amount.toFixed(2);
  }
  return `${currency} ${amount}`;
}

export function currencySymbol(currency: string): string {
  if (currency === "INR") return "₹";
  if (currency === "USD") return "$";
  return currency + " ";
}
