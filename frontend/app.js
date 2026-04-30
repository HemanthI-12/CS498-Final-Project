const API_BASE_URL = 'http://localhost:5000/api';

const fetchData = async (endpoint, params = {}) => {
    try {
        const queryString = new URLSearchParams(params).toString();
        const url = `${API_BASE_URL}${endpoint}${queryString ? '?' + queryString : ''}`;
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
    } catch (error) {
        throw error;
    }
};

const revealDelay = (idx) => ({ animationDelay: `${idx * 65 + 120}ms` });
//HEADER
const Header = () => {
    return (
        <header className="hero-block">
            <div className="max-w-7xl mx-auto px-6 hero-grid">
                <div className="glass-panel">
                    <div className="hero-ribbon">
                        <span>AirBnB Data Experience</span>
                    </div>
                    <h1 className="hero-title">AirBnB Analytics Lab</h1>
                    <div className="hero-meta">
                        <span className="meta-pill">Supports: Portland, Salem, Los Angeles, San Diego</span>
                    </div>
                </div>
            </div>
            <div className="hero-layer"></div>
        </header>
    );
};

// ============================
// Component: Query 1 - Listings Search
// ============================
const Query1Listings = () => {
    const [data, setData] = React.useState(null);
    const [loading, setLoading] = React.useState(false);
    const [error, setError] = React.useState(null);
    const [city, setCity] = React.useState('Portland');
    const [startDate, setStartDate] = React.useState('2024-03-15');
    const [endDate, setEndDate] = React.useState('2024-03-16');
    const validCities = ['Portland', 'Salem', 'Los Angeles', 'San Diego'];

    const handleSearch = async (e) => {
        e.preventDefault();
        setError(null);

        if (!validCities.includes(city)) {
            setError('Please choose one of the supported cities.');
            return;
        }

        setLoading(true);
        try {
            const result = await fetchData('/query1/listings', {
                city,
                start_date: startDate,
                end_date: endDate,
            });
            setData(result);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="glass-panel mb-8 reveal max-w-6xl mx-auto" style={{ animationDelay: '80ms' }}>
            <div className="flex flex-col gap-5 mb-6">
                <div className="status-pill">Search available listings by date and rating</div>
                <div className="flex items-center gap-3 flex-wrap">
                    <h2 className="text-3xl font-bold">Listings Search</h2>
                </div>
            </div>

            <form onSubmit={handleSearch} className="glass-panel mb-8">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div>
                        <label className="label-fine">City</label>
                        <select value={city} onChange={(e) => setCity(e.target.value)} className="field-box">
                            {validCities.map((option) => (
                                <option key={option} value={option}>{option}</option>
                            ))}
                        </select>
                    </div>
                    <div>
                        <label className="label-fine">Start Date</label>
                        <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className="field-box" />
                    </div>
                    <div>
                        <label className="label-fine">End Date</label>
                        <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className="field-box" />
                    </div>
                    <div className="flex items-end">
                        <button type="submit" className="btn-solid btn-primary w-full" disabled={loading}>
                            {loading ? 'Searching…' : 'Run search'}
                        </button>
                    </div>
                </div>
            </form>

            {error && <div className="glass-panel status-pill text-red-200 bg-black/10 border-red-400">{error}</div>}

            {loading && (
                <div className="flex justify-center py-12">
                    <div className="loader"></div>
                </div>
            )}

            {data && (
                <div className="space-y-6">
                    <div className="glass-panel status-pill bg-white/5 border-white/10 text-slate-100">
                        Found {data.count} listings in {data.city}
                    </div>

                    <div className="grid gap-6">
                        {data.listings.map((listing, idx) => (
                            <div key={idx} className="glass-card reveal" style={revealDelay(idx)}>
                                <div className="flex flex-col md:flex-row md:justify-between gap-4 mb-4">
                                    <div>
                                        <h3 className="text-2xl font-semibold">{listing.name}</h3>
                                        <p className="text-sm text-slate-400 mt-1">{listing.neighborhood} • {listing.room_type}</p>
                                    </div>
                                    <div className="status-pill bg-gradient-to-r from-cyan-400 to-blue-400 text-slate-950">
                                        ⭐ {listing.rating?.toFixed(1) ?? 'N/A'}
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 mb-4">
                                    <div className="glass-panel text-slate-100 bg-white/5 border-white/10">
                                        <p className="text-xs uppercase tracking-[0.18em] text-slate-400">Guests</p>
                                        <p className="text-xl font-semibold">{listing.accommodates}</p>
                                    </div>
                                    <div className="glass-panel text-slate-100 bg-white/5 border-white/10">
                                        <p className="text-xs uppercase tracking-[0.18em] text-slate-400">Property</p>
                                        <p className="text-xl font-semibold">{listing.property_type}</p>
                                    </div>
                                    <div className="glass-panel text-slate-100 bg-white/5 border-white/10">
                                        <p className="text-xs uppercase tracking-[0.18em] text-slate-400">Price/night</p>
                                        <p className="text-xl font-semibold">${listing.price?.toFixed(2)}</p>
                                    </div>
                                    <div className="glass-panel text-slate-100 bg-white/5 border-white/10">
                                        <p className="text-xs uppercase tracking-[0.18em] text-slate-400">Amenities</p>
                                        <p className="mt-2 text-sm leading-6">
                                            {listing.amenities?.slice(0, 4).join(' • ') || 'None'}
                                        </p>
                                    </div>
                                </div>

                                <p className="text-slate-300 leading-7 mb-4">{listing.description}</p>
                                <a href={listing.listing_url} target="_blank" rel="noreferrer" className="btn-solid btn-secondary">
                                    Open listing
                                </a>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

// ============================
// Component: Query 2 - Neighborhoods with no listings
// ============================
const Query2Neighborhoods = () => {
    const [data, setData] = React.useState(null);
    const [loading, setLoading] = React.useState(false);
    const [error, setError] = React.useState(null);
    const [month, setMonth] = React.useState('2024-03');

    const handleSearch = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        try {
            const result = await fetchData('/query2/neighborhoods', { month });
            setData(result);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="glass-panel mb-8 reveal max-w-6xl mx-auto" style={{ animationDelay: '100ms' }}>
            <div className="flex flex-col gap-5 mb-6">
                <div className="flex flex-wrap items-center gap-3">
                    <h2 className="text-3xl font-bold">No-listing Zones</h2>
                </div>
            </div>

            <form onSubmit={handleSearch} className="glass-panel mb-8">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                        <label className="label-fine">Month</label>
                        <input type="month" value={month} onChange={(e) => setMonth(e.target.value)} className="field-box" />
                    </div>
                    <div className="md:col-span-2 flex items-end">
                        <button type="submit" className="btn-solid btn-primary w-full" disabled={loading}>
                            {loading ? 'Finding...' : 'Reveal neighborhoods'}
                        </button>
                    </div>
                </div>
            </form>

            {error && <div className="glass-panel status-pill text-red-200 bg-black/10 border-red-400">{error}</div>}

            {loading && (
                <div className="flex justify-center py-12">
                    <div className="loader"></div>
                </div>
            )}

            {data && (
                <div className="space-y-6">
                    <div className="glass-panel status-pill bg-white/5 border-white/10 text-slate-100">
                        {data.count} neighborhoods without listings in {data.month}
                    </div>
                    <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-2">
                        {data.neighborhoods.map((item, idx) => (
                            <div key={idx} className="glass-card reveal" style={revealDelay(idx)}>
                                <p className="text-sm uppercase tracking-[0.22em] text-slate-500 mb-2">{item.city}</p>
                                <h3 className="text-xl font-semibold">{item.neighborhood}</h3>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};


const Query3Availability = () => {
    const [data, setData] = React.useState(null);
    const [loading, setLoading] = React.useState(false);
    const [error, setError] = React.useState(null);
    const [month, setMonth] = React.useState('2024-03');

    const handleSearch = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        try {
            const result = await fetchData('/query3/availability', { month });
            setData(result);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="glass-panel mb-8 reveal max-w-6xl mx-auto" style={{ animationDelay: '120ms' }}>
            <div className="flex flex-col gap-5 mb-6">
                <div className="flex flex-wrap items-center gap-3">
                    <h2 className="text-3xl font-bold">Booking Windows</h2>
                </div>
            </div>

            <form onSubmit={handleSearch} className="glass-panel mb-8">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                        <label className="label-fine">Month</label>
                        <input type="month" value={month} onChange={(e) => setMonth(e.target.value)} className="field-box" />
                    </div>
                    <div className="md:col-span-2 flex items-end">
                        <button type="submit" className="btn-solid btn-primary w-full" disabled={loading}>
                            {loading ? 'Checking…' : 'Check Availability'}
                        </button>
                    </div>
                </div>
            </form>

            {error && <div className="glass-panel status-pill text-red-200 bg-black/10 border-red-400">{error}</div>}
            {loading && (
                <div className="flex justify-center py-12">
                    <div className="loader"></div>
                </div>
            )}

            {data && (
                <div className="space-y-6">
                    <div className="glass-panel status-pill bg-white/5 border-white/10 text-slate-100">
                        {data.count} Salem listings for {data.month}
                    </div>
                    <div className="grid gap-5">
                        {data.listings.map((listing, idx) => (
                            <div key={idx} className="glass-card reveal" style={revealDelay(idx)}>
                                <h3 className="text-2xl font-semibold mb-3">{listing.name}</h3>
                                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 mb-4">
                                    <div className="glass-panel bg-white/5 border-white/10">
                                        <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Min nights</p>
                                        <p className="text-xl font-semibold">{listing.min_nights}</p>
                                    </div>
                                    <div className="glass-panel bg-white/5 border-white/10">
                                        <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Max nights</p>
                                        <p className="text-xl font-semibold">{listing.max_nights}</p>
                                    </div>
                                    <div className="glass-panel bg-white/5 border-white/10">
                                        <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Month</p>
                                        <p className="text-xl font-semibold">{listing.month}</p>
                                    </div>
                                    <div className="glass-panel bg-white/5 border-white/10">
                                        <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Blocks</p>
                                        <p className="text-xl font-semibold">{listing.availability_periods.length}</p>
                                    </div>
                                </div>
                                {listing.availability_periods.length ? (
                                    <div className="grid gap-3">
                                        {listing.availability_periods.map((period, i) => (
                                            <div key={i} className="glass-panel bg-gradient-to-r from-cyan-500/10 via-transparent to-white/10 border-white/10">
                                                <div className="flex justify-between gap-4 items-center">
                                                    <span className="font-semibold">{period.from} → {period.to}</span>
                                                    <span className="status-pill bg-white/10 text-slate-100">{period.nights} nights</span>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <p className="text-slate-400 italic">No bookable runs found for this listing.</p>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};


const Query4BookingTrend = () => {
    const [data, setData] = React.useState(null);
    const [loading, setLoading] = React.useState(false);
    const [error, setError] = React.useState(null);
    const [year, setYear] = React.useState(2024);

    const handleSearch = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        try {
            const result = await fetchData('/query4/booking-trend', { year });
            setData(result);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const maxNights = data?.trend ? Math.max(...data.trend.map((m) => m.available_nights)) : 0;

    return (
        <div className="glass-panel mb-8 reveal" style={{ animationDelay: '140ms' }}>
            <div className="flex flex-col gap-5 mb-6">
                <div className="flex flex-wrap items-center gap-3">
                    <h2 className="text-3xl font-bold">Month Trend</h2>
                    <span className="status-pill">March–August</span>
                </div>
            </div>

            <form onSubmit={handleSearch} className="glass-panel mb-8">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                        <label className="label-fine">Year</label>
                        <input type="number" value={year} onChange={(e) => setYear(parseInt(e.target.value))} className="field-box" />
                    </div>
                    <div className="md:col-span-2 flex items-end">
                        <button type="submit" className="btn-solid btn-primary w-full" disabled={loading}>
                            {loading ? 'Loading…' : 'Show trend'}
                        </button>
                    </div>
                </div>
            </form>

            {error && <div className="glass-panel status-pill text-red-200 bg-black/10 border-red-400">{error}</div>}
            {loading && (
                <div className="flex justify-center py-12">
                    <div className="loader"></div>
                </div>
            )}

            {data && (
                <div className="space-y-4">
                    <div className="glass-panel status-pill bg-white/5 border-white/10 text-slate-100">
                        Total available nights by month for {data.city}, {data.year}
                    </div>
                    <div className="space-y-4">
                        {data.trend.map((month, idx) => (
                            <div key={idx} className="glass-panel bg-white/5 border-white/10 p-4">
                                <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3">
                                    <div>
                                        <p className="text-sm uppercase tracking-[0.18em] text-slate-500">{month.month}</p>
                                        <p className="text-xl font-semibold">{month.available_nights.toLocaleString()} nights</p>
                                    </div>
                                    <div className="w-full sm:w-2/3 bg-slate-900/70 rounded-full h-4 overflow-hidden">
                                        <div
                                            className="h-full rounded-full bg-gradient-to-r from-orange-400 to-orange-600 transition-all"
                                            style={{ width: `${maxNights > 0 ? (month.available_nights / maxNights) * 100 : 0}%` }}
                                        />
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

const Query5ReviewTrend = () => {
    const [data, setData] = React.useState(null);
    const [loading, setLoading] = React.useState(false);
    const [error, setError] = React.useState(null);

    const handleSearch = async () => {
        setLoading(true);
        setError(null);
        try {
            const result = await fetchData('/query5/review-trend');
            setData(result);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    React.useEffect(() => {
        handleSearch();
    }, []);

    return (
        <div className="glass-panel mb-8 reveal" style={{ animationDelay: '160ms' }}>
            <div className="flex flex-col gap-5 mb-6">
                <div className="flex flex-wrap items-center gap-3">
                    <h2 className="text-3xl font-bold">Yearly December Trend</h2>
                </div>
            </div>

            {error && <div className="glass-panel status-pill text-red-200 bg-black/10 border-red-400">{error}</div>}
            {loading && (
                <div className="flex justify-center py-12">
                    <div className="loader"></div>
                </div>
            )}

            {data && (
                <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
                    {Object.entries(data.trend).map(([city, cityData], idx) => (
                        <div key={city} className="glass-card reveal" style={revealDelay(idx)}>
                            <h3 className="text-2xl font-semibold mb-4">{city}</h3>
                            <div className="space-y-3">
                                {Object.entries(cityData.december_reviews)
                                    .sort((a, b) => parseInt(a[0]) - parseInt(b[0]))
                                    .map(([year, count]) => (
                                        <div key={year} className="flex items-center justify-between bg-white/10 p-3 rounded-xl border border-white/10">
                                            <span className="text-sm text-slate-300">{year}</span>
                                            <span className="status-pill bg-amber-400/15 text-amber-200">{count}</span>
                                        </div>
                                    ))}
                                {Object.keys(cityData.december_reviews).length === 0 && (
                                    <p className="text-slate-400 italic">No December reviews yet.</p>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};


const Query6RepeatBookings = () => {
    const [data, setData] = React.useState(null);
    const [loading, setLoading] = React.useState(false);
    const [error, setError] = React.useState(null);

    const handleSearch = async () => {
        setLoading(true);
        setError(null);
        try {
            const result = await fetchData('/query6/repeat-bookings');
            setData(result);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    React.useEffect(() => {
        handleSearch();
    }, []);

    return (
        <div className="glass-panel mb-8 reveal" style={{ animationDelay: '180ms' }}>
            <div className="flex flex-col gap-5 mb-6">
                <div className="flex flex-wrap items-center gap-3">
                    <h2 className="text-3xl font-bold">Potential Future Leads</h2>
                </div>
            </div>

            {error && <div className="glass-panel status-pill text-red-200 bg-black/10 border-red-400">{error}</div>}
            {loading && (
                <div className="flex justify-center py-12">
                    <div className="loader"></div>
                </div>
            )}

            {data && (
                <div className="space-y-5">
                    <div className="glass-panel status-pill bg-white/5 border-white/10 text-slate-100">
                        {data.count} listings found with repeat-review signals
                    </div>
                    <div className="grid gap-5">
                        {data.repeat_bookings.map((booking, idx) => (
                            <div key={idx} className="glass-card reveal" style={revealDelay(idx)}>
                                <div className="flex flex-col xl:flex-row xl:justify-between xl:items-start gap-3 mb-4">
                                    <div>
                                        <h3 className="text-2xl font-semibold">{booking.listing_name}</h3>
                                        <p className="text-sm text-slate-400 mt-1">Host: {booking.host_name}</p>
                                    </div>
                                    <span className="status-pill bg-cyan-500/15 text-cyan-100">{booking.month}</span>
                                </div>

                                <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4 mb-4">
                                    <div className="glass-panel bg-white/5 border-white/10">
                                        <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Reviewer</p>
                                        <p className="text-base font-semibold">{booking.reviewer_name}</p>
                                    </div>
                                    <div className="glass-panel bg-white/5 border-white/10">
                                        <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Booked before</p>
                                        <p className="text-base font-semibold">Yes</p>
                                    </div>
                                    <div className="glass-panel bg-white/5 border-white/10">
                                        <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Min nights</p>
                                        <p className="text-base font-semibold">{booking.min_nights}</p>
                                    </div>
                                    <div className="glass-panel bg-white/5 border-white/10">
                                        <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Max nights</p>
                                        <p className="text-base font-semibold">{booking.max_nights}</p>
                                    </div>
                                </div>

                                <p className="text-slate-300 leading-7 mb-4">{booking.description}</p>
                                {booking.other_listings.length > 0 && (
                                    <div className="glass-panel bg-white/5 border-white/10 p-4 mb-4">
                                        <p className="text-sm uppercase tracking-[0.14em] text-slate-400 mb-2">other listings by host</p>
                                        <ul className="space-y-2 text-slate-300">
                                            {booking.other_listings.map((item, i) => (
                                                <li key={i}>• {item.name}</li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                                <a href={booking.listing_url} target="_blank" rel="noreferrer" className="btn-solid btn-secondary">
                                    Inspect listing
                                </a>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};


const App = () => {
    const [activeTab, setActiveTab] = React.useState(0);

    const tabs = [
        { name: 'Listings Search', component: Query1Listings },
        { name: 'Empty Neighborhoods', component: Query2Neighborhoods },
        { name: 'Availability', component: Query3Availability },
        { name: 'Monthly Trends', component: Query4BookingTrend },
        { name: 'Reviews', component: Query5ReviewTrend },
        { name: 'Repeat Bookings', component: Query6RepeatBookings },
    ];

    const CurrentComponent = tabs[activeTab].component;

    return (
        <div className="min-h-screen app-shell">
            <Header />

            <main className="max-w-7xl mx-auto px-6 py-12">
                <div className="glass-panel mb-8 tab-strip reveal" style={{ animationDelay: '60ms' }}>
                    {tabs.map((tab, idx) => (
                        <button key={idx} onClick={() => setActiveTab(idx)} className={`tab-button ${activeTab === idx ? 'active' : ''}`}>
                            {tab.name}
                        </button>
                    ))}
                </div>

                <CurrentComponent />
            </main>
        </div>
    );
};

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
