/**
 * Typed Redux Hooks
 * 
 * Pre-typed versions of useDispatch and useSelector hooks for type safety.
 * Use these instead of the plain hooks from react-redux.
 * 
 * @see https://redux-toolkit.js.org/tutorials/typescript#define-typed-hooks
 */

import { useDispatch, useSelector } from 'react-redux';
import type { TypedUseSelectorHook } from 'react-redux';
import type { RootState, AppDispatch } from './index';

// Typed dispatch hook
export const useAppDispatch = () => useDispatch<AppDispatch>();

// Typed selector hook
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
