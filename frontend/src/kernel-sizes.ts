export const BOX_SIZES = [3, 5, 7, 9, 11, 21, 31] as const;
export const DERIVATIVE_SIZES = [3, 5, 7, 9, 11] as const;
export const sizesFor = (operation: string): readonly number[] => operation === 'blur' || operation === 'sharpen' ? BOX_SIZES : DERIVATIVE_SIZES;
