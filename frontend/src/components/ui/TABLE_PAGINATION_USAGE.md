# Table Pagination Component Usage

The `TablePagination` component is a reusable pagination component that can be used with any table that receives paginated data from a backend API.

## Interface

```typescript
interface PaginationData {
  count: number;        // Total number of items
  next: string | null;  // URL for next page (null if no next page)
  previous: string | null; // URL for previous page (null if no previous page)
  results: any[];       // Array of results for current page
}

interface TablePaginationProps {
  paginationData: PaginationData;
  currentPage: number;
  pageSize?: number;    // Default: 25
  onPageChange: (page: number) => void;
  isLoading?: boolean;  // Default: false
}
```

## Usage Example

```typescript
import { TablePagination, PaginationData } from '@/components/ui/table-pagination';

const MyTableComponent = () => {
  const [currentPage, setCurrentPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [paginationData, setPaginationData] = useState<PaginationData>({
    count: 0,
    next: null,
    previous: null,
    results: [],
  });

  const loadData = async (page: number = 1) => {
    try {
      setLoading(true);
      const response = await MyAPI.getAll({ page });
      const responseData = response.data;
      
      if (responseData && 'results' in responseData) {
        setPaginationData(responseData);
        setCurrentPage(page);
      }
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePageChange = (newPage: number) => {
    loadData(newPage);
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
      {/* Your table content here */}
      <table className="w-full">
        {/* ... table headers and rows ... */}
      </table>
      
      {/* Pagination */}
      <TablePagination
        paginationData={paginationData}
        currentPage={currentPage}
        onPageChange={handlePageChange}
        isLoading={loading}
        pageSize={25} // Optional, defaults to 25
      />
    </div>
  );
};
```

## Features

- **Responsive Design**: Adapts to mobile and desktop screens
- **Rich Pagination**: Uses `react-paginate` for professional pagination controls
- **Loading States**: Shows loading indicator and disables controls during loading
- **Flexible**: Works with any paginated API response that follows the Django REST framework pagination format
- **Accessible**: Proper ARIA labels and keyboard navigation
- **Customizable**: Accepts optional `pageSize` parameter

## Backend Compatibility

This component is designed to work with Django REST framework's `PageNumberPagination`, which returns responses in this format:

```json
{
  "count": 100,
  "next": "http://api.example.org/accounts/?page=2",
  "previous": null,
  "results": [...]
}
```

## Styling

The component uses Tailwind CSS classes and follows the design system established in your application. All pagination controls are styled consistently with your existing UI components.