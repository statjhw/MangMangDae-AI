import { motion } from 'framer-motion';
import { forwardRef, SelectHTMLAttributes, useState } from 'react';
import { clsx } from 'clsx';
import { ChevronDown, Check } from 'lucide-react';

interface SelectOption {
  value: string;
  label: string;
}

interface SelectProps extends Omit<SelectHTMLAttributes<HTMLSelectElement>, 'onChange'> {
  label?: string;
  error?: string;
  helperText?: string;
  options: SelectOption[];
  placeholder?: string;
  onChange?: (value: string) => void;
  className?: string;
}

const Select = forwardRef<HTMLSelectElement, SelectProps>(({
  label,
  error,
  helperText,
  options,
  placeholder = '선택해주세요',
  onChange,
  className,
  value,
  ...props
}, ref) => {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedValue, setSelectedValue] = useState(value || '');

  const selectedOption = options.find(option => option.value === selectedValue);

  const handleSelect = (option: SelectOption) => {
    setSelectedValue(option.value);
    setIsOpen(false);
    onChange?.(option.value);
  };

  return (
    <div className="relative">
      {label && (
        <label className="block text-sm font-medium text-secondary-700 mb-2">
          {label}
        </label>
      )}
      
      <div className="relative">
        <motion.button
          type="button"
          className={clsx(
            'w-full px-4 py-3 border rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-0',
            'flex items-center justify-between',
            error 
              ? 'border-red-300 focus:ring-red-500 focus:border-red-500' 
              : 'border-secondary-300 focus:ring-primary-500 focus:border-primary-500',
            className
          )}
          onClick={() => setIsOpen(!isOpen)}
          whileHover={{ scale: 1.01 }}
          whileTap={{ scale: 0.99 }}
        >
          <span className={selectedOption ? 'text-secondary-900' : 'text-secondary-400'}>
            {selectedOption ? selectedOption.label : placeholder}
          </span>
          <motion.div
            animate={{ rotate: isOpen ? 180 : 0 }}
            transition={{ duration: 0.2 }}
          >
            <ChevronDown className="h-5 w-5 text-secondary-400" />
          </motion.div>
        </motion.button>
        
        {/* 드롭다운 메뉴 */}
        {isOpen && (
          <motion.div
            className="absolute z-10 w-full mt-1 bg-white border border-secondary-200 rounded-lg shadow-lg max-h-60 overflow-y-auto"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
          >
            {options.map((option) => (
              <button
                key={option.value}
                type="button"
                className={clsx(
                  'w-full px-4 py-2 text-left transition-colors duration-150 flex items-center justify-between',
                  option.value === selectedValue
                    ? 'bg-primary-50 text-primary-700'
                    : 'hover:bg-secondary-50'
                )}
                onClick={() => handleSelect(option)}
              >
                <span>{option.label}</span>
                {option.value === selectedValue && (
                  <Check className="h-4 w-4 text-primary-600" />
                )}
              </button>
            ))}
          </motion.div>
        )}
      </div>
      
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
      
      {/* 숨겨진 select 요소 (접근성용) */}
      <select
        ref={ref}
        value={selectedValue}
        onChange={(e) => handleSelect({ value: e.target.value, label: e.target.value })}
        className="sr-only"
        {...props}
      >
        <option value="">{placeholder}</option>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
});

Select.displayName = 'Select';

export default Select; 