// Configuration
const API_BASE_URL = 'http://localhost:8000';
const API_TIMEOUT = 10000; // 10 seconds

// Import validation utilities
const Validation = {
    // Username: 3-20 alphanumeric chars, underscores, and hyphens
    username: (value) => /^[a-zA-Z0-9_-]{3,20}$/.test(value),
    
    // Password: 8+ chars, 1 letter, 1 number, 1 special char
    password: (value) => /^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$/.test(value),
    
    // Email: standard email format
    email: (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value),
    
    // Word: 5 letters only
    word: (value) => /^[A-Za-z]{5}$/.test(value),
    
    // Sanitize input to prevent XSS
    sanitize: (input) => {
        if (!input) return '';
        return input
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#x27;');
    }
};

// Error class for API errors
class APIError extends Error {
    constructor(message, status, code) {
        super(message);
        this.name = 'APIError';
        this.status = status;
        this.code = code;
    }
}

class APIClient {
    constructor() {
        this.token = localStorage.getItem('authToken');
    }

    async request(endpoint, options = {}) {
        // Input validation
        if (!endpoint || typeof endpoint !== 'string') {
            throw new Error('Endpoint must be a valid string');
        }

        // Create AbortController for request timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);

        const url = `${API_BASE_URL}${endpoint}`;
        const config = {
            signal: controller.signal,
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                ...options.headers,
            },
            ...options,
        };

        // Add auth token if exists
        if (this.token && !config.headers.Authorization) {
            config.headers.Authorization = `Bearer ${this.token}`;
        }

        if (this.token && !config.headers.Authorization) {
            config.headers.Authorization = `Bearer ${this.token}`;
        }

        try {
            // Skip health check for health endpoint to avoid infinite loop
            // if (endpoint !== '/health') {
            //     try {
            //         const healthCheck = await this.request('/health', { method: 'GET' });
            //         if (!healthCheck.ok) {
            //             throw new APIError('Backend server is not responding properly', 503, 'SERVICE_UNAVAILABLE');
            //         }
            //     } catch (networkError) {
            //         if (networkError.name === 'AbortError') {
            //             throw new APIError('Request timeout. Please check your connection and try again.', 504, 'REQUEST_TIMEOUT');
            //         }
            //         throw new APIError('Unable to connect to the backend server. Please try again later.', 503, 'SERVICE_UNAVAILABLE');
            //     }
            // }

            const response = await fetch(url, config);
            clearTimeout(timeoutId);
            
            // Handle non-JSON responses
            let data;
            const contentType = response.headers.get('content-type');
            
            if (contentType && contentType.includes('application/json')) {
                data = await response.json();
            } else {
                const text = await response.text();
                throw new APIError(
                    text || 'Invalid response format', 
                    response.status, 
                    'INVALID_RESPONSE'
                );
            }

            if (!response.ok) {
                // Log error for debugging
                console.error('API Error:', {
                    url,
                    status: response.status,
                    error: data,
                    timestamp: new Date().toISOString()
                });
                
                // Extract error details
                const errorMessage = data.detail || data.message || 'An unexpected error occurred';
                const errorCode = data.code || `HTTP_${response.status}`;
                
                // Handle rate limiting
                if (response.status === 429) {
                    const retryAfter = response.headers.get('Retry-After') || '60';
                    throw new APIError(
                        `Too many requests. Please try again in ${retryAfter} seconds.`,
                        response.status,
                        'RATE_LIMIT_EXCEEDED',
                        { retryAfter: parseInt(retryAfter, 10) }
                    );
                }
                
                // Handle other errors
                throw new APIError(errorMessage, response.status, errorCode);
            }

            return data;
        } catch (error) {
            console.error('API request failed:', error);
            
            // Handle different types of errors
            let userFriendlyError = {
                message: 'An unexpected error occurred. Please try again.',
                code: 'UNKNOWN_ERROR',
                status: 500
            };
            
            if (error.name === 'AbortError') {
                userFriendlyError = {
                    message: 'Request timed out. Please check your connection and try again.',
                    code: 'REQUEST_TIMEOUT',
                    status: 504
                };
            } else if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
                userFriendlyError = {
                    message: 'Unable to connect to the server. Please check your internet connection.',
                    code: 'NETWORK_ERROR',
                    status: 0
                };
            } else if (error instanceof APIError) {
                userFriendlyError = {
                    message: error.message,
                    code: error.code,
                    status: error.status
                };
            }
            
            // Show error to user (could be replaced with a toast notification)
            if (typeof window !== 'undefined' && window.showError) {
                window.showError(userFriendlyError.message);
            } else {
                console.error('Error:', userFriendlyError.message);
            }
            
            // Re-throw the error with user-friendly message
            throw new APIError(
                userFriendlyError.message,
                userFriendlyError.status,
                userFriendlyError.code
            );
        }
    }

    async registerUser(username, password, email = null) {
        // Input validation
        if (!Validation.username(username)) {
            throw new APIError(
                'Username must be 3-20 characters long and can only contain letters, numbers, underscores, and hyphens.',
                400,
                'INVALID_USERNAME'
            );
        }
        
        if (!Validation.password(password)) {
            throw new APIError(
                'Password must be at least 8 characters long and include at least one letter, one number, and one special character.',
                400,
                'INVALID_PASSWORD'
            );
        }
        
        // Sanitize inputs
        const sanitizedUsername = Validation.sanitize(username);
        const sanitizedEmail = email ? Validation.sanitize(email) : null;

        try {
            const data = await this.request('/api/v1/auth/register', {
                method: 'POST',
                body: JSON.stringify({ 
                    username: sanitizedUsername, 
                    password, 
                    email: sanitizedEmail
                }),
            });
            
            if (data.token) {
                this.token = data.token;
                localStorage.setItem('authToken', data.token);
                if (data.user) {
                    localStorage.setItem('username', data.user.username || '');
                }
            }
            
            return data;
        } catch (error) {
            console.error('Registration failed:', error);
            throw error;
        }
    }

    async loginUser(username, password) {
        // Input validation
        if (!username || !password) {
            throw new APIError(
                'Username and password are required.',
                400,
                'MISSING_CREDENTIALS'
            );
        }
        
        // Sanitize username
        const sanitizedUsername = Validation.sanitize(username);
        
        try {
            const data = await this.request('/api/users/login', {
                method: 'POST',
                body: JSON.stringify({ 
                    username: sanitizedUsername, 
                    password 
                }),
            });
            
            if (data.token) {
                this.token = data.token;
                localStorage.setItem('authToken', data.token);
                if (data.user) {
                    localStorage.setItem('userName', data.user.name || '');
                    localStorage.setItem('userUsername', data.user.username || '');
                }
            }
            
            return data;
        } catch (error) {
            console.error('Login failed:', error);
            
            // Handle specific login errors
            if (error.status === 401) {
                throw new APIError(
                    'Invalid username or password. Please try again.',
                    401,
                    'INVALID_CREDENTIALS'
                );
            }
            
            throw error;
        }
    }

    async loginAdmin(username, password) {
        const data = await this.request('/api/admin/login', {
            method: 'POST',
            body: JSON.stringify({ username, password }),
        });
        
        if (data.token) {
            this.token = data.token;
            localStorage.setItem('adminToken', data.token);
            localStorage.setItem('adminLoggedIn', 'true');
        }
        
        return data;
    }

    async saveGameResult(username, gameData) {
        // Input validation
        if (!username || typeof username !== 'string') {
            throw new Error('Username is required and must be a string');
        }
        
        if (!gameData || typeof gameData !== 'object') {
            throw new Error('Game data is required and must be an object');
        }
        
        try {
            // Validate game data structure
            const requiredFields = ['targetWord', 'attempts', 'won', 'timeSpent'];
            const missingFields = requiredFields.filter(field => !(field in gameData));
            
            if (missingFields.length > 0) {
                throw new APIError(
                    `Missing required game data: ${missingFields.join(', ')}`,
                    400,
                    'INVALID_GAME_DATA'
                );
            }
            
            // Sanitize inputs
            const sanitizedUsername = Validation.sanitize(username);
            const sanitizedGameData = {
                ...gameData,
                targetWord: Validation.sanitize(gameData.targetWord),
                attempts: gameData.attempts.map(attempt => ({
                    ...attempt,
                    word: Validation.sanitize(attempt.word)
                }))
            };
            
            return await this.request(`/api/games/save?username=${encodeURIComponent(sanitizedUsername)}`, {
                method: 'POST',
                body: JSON.stringify(sanitizedGameData),
            });
        } catch (error) {
            console.error('Failed to save game result:', error);
            throw error;
        }
    }

    async getUserGames(username) {
        return await this.request(`/api/games/user/${username}`);
    }

    async getUserProfile(username) {
        return await this.request(`/api/users/profile/${username}`);
    }

    async getDashboardStats() {
        return await this.request('/api/admin/dashboard');
    }

    async getUserDetails(username) {
        return await this.request(`/api/admin/user-details/${username}`);
    }

    async clearAllData() {
        return await this.request('/api/admin/clear-data', {
            method: 'DELETE',
        });
    }

    async exportData() {
        return await this.request('/api/admin/export-data');
    }

    async getLeaderboard() {
        return await this.request('/api/games/leaderboard');
    }

    logout() {
        this.token = null;
        localStorage.removeItem('authToken');
        localStorage.removeItem('adminToken');
        localStorage.removeItem('userName');
        localStorage.removeItem('userMobile');
        localStorage.removeItem('adminLoggedIn');
    }
}

const api = new APIClient();
