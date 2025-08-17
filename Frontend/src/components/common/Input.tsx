import { motion } from 'framer-motion';
import { forwardRef, InputHTMLAttributes, useState, useEffect } from 'react';
import { clsx } from 'clsx';
import { Eye, EyeOff, Search } from 'lucide-react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  variant?: 'default' | 'search';
  suggestions?: string[];
  onSuggestionSelect?: (suggestion: string) => void;
}

const Input = forwardRef<HTMLInputElement, InputProps>(({
  label,
  error,
  helperText,
  leftIcon,
  rightIcon,
  variant = 'default',
  suggestions = [],
  onSuggestionSelect,
  className,
  type = 'text',
  ...props
}, ref) => {
  const [showPassword, setShowPassword] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [inputValue, setInputValue] = useState(props.value || '');

  // 외부 value 변경 감지
  useEffect(() => {
    setInputValue(props.value || '');
  }, [props.value]);

  const inputType = type === 'password' && showPassword ? 'text' : type;

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setInputValue(newValue);
    setShowSuggestions(suggestions.length > 0 && newValue.length > 0);
    props.onChange?.(e);
  };

  const handleSuggestionClick = (suggestion: string) => {
    setInputValue(suggestion);
    setShowSuggestions(false);
    onSuggestionSelect?.(suggestion);
    
    // onChange도 호출하여 form 상태 업데이트
    if (props.onChange) {
      const mockEvent = {
        target: { value: suggestion }
      } as React.ChangeEvent<HTMLInputElement>;
      props.onChange(mockEvent);
    }
  };

  return (
    <div className="relative">
      {label && (
        <label className="block text-sm font-medium text-secondary-700 mb-2">
          {label}
        </label>
      )}
      
      <div className="relative">
        {leftIcon && (
          <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-secondary-400">
            {leftIcon}
          </div>
        )}
        
        <input
          ref={ref}
          type={inputType}
          className={clsx(
            'w-full px-4 py-3 border rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-0',
            'placeholder-secondary-400',
            leftIcon && 'pl-10',
            rightIcon && 'pr-10',
            variant === 'search' && 'pl-10',
            error 
              ? 'border-red-300 focus:ring-red-500 focus:border-red-500' 
              : 'border-secondary-300 focus:ring-primary-500 focus:border-primary-500',
            className
          )}
          value={inputValue}
          onChange={handleInputChange}
          onFocus={() => setShowSuggestions(suggestions.length > 0 && String(inputValue).length > 0)}
          onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
          {...props}
        />
        
        {variant === 'search' && !leftIcon && (
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-secondary-400" />
        )}
        
        {rightIcon && (
          <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-secondary-400">
            {rightIcon}
          </div>
        )}
        
        {type === 'password' && (
          <button
            type="button"
            className="absolute right-3 top-1/2 transform -translate-y-1/2 text-secondary-400 hover:text-secondary-600"
            onClick={() => setShowPassword(!showPassword)}
          >
            {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
          </button>
        )}
      </div>
      
      {/* 자동완성 제안 */}
      {showSuggestions && suggestions.length > 0 && (
        <motion.div
          className="absolute z-10 w-full mt-1 bg-white border border-secondary-200 rounded-lg shadow-lg max-h-60 overflow-y-auto"
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
        >
          {suggestions.map((suggestion, index) => (
            <button
              key={index}
              type="button"
              className="w-full px-4 py-2 text-left hover:bg-secondary-50 transition-colors duration-150"
              onClick={() => handleSuggestionClick(suggestion)}
            >
              {suggestion}
            </button>
          ))}
        </motion.div>
      )}
      
      {error && (
        <motion.p
          className="mt-1 text-sm text-red-600"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          {error}
        </motion.p>
      )}
      
      {helperText && !error && (
        <p className="mt-1 text-sm text-secondary-500">
          {helperText}
        </p>
      )}
    </div>
  );
});

Input.displayName = 'Input';

export default Input; 