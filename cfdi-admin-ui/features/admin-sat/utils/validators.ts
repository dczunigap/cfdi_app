const RFC_REGEX = /^[A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3}$/;
const PHONE_REGEX = /^\d{8,15}$/;

export const normalizeRfc = (value: string) => value.trim().toUpperCase();
export const normalizePhone = (value: string) => value.replace(/\D+/g, "");

export const isValidRfc = (value: string) => RFC_REGEX.test(normalizeRfc(value));
export const isValidPhone = (value: string) => PHONE_REGEX.test(normalizePhone(value));
