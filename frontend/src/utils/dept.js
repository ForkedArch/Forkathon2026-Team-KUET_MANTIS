/**
 * Official KUET Department Mapping and Formatter
 * Khulna University of Engineering & Technology (KUET)
 */

export const KUET_DEPTS = {
  '01': { code: 'CE', name: 'Civil Engineering' },
  '02': { code: 'EEE', name: 'Electrical & Electronic Engineering' },
  '03': { code: 'EEE', name: 'Electrical & Electronic Engineering' },
  '04': { code: 'ME', name: 'Mechanical Engineering' },
  '05': { code: 'ME', name: 'Mechanical Engineering' },
  '06': { code: 'ECE', name: 'Electronics & Communication Engineering' },
  '07': { code: 'CSE', name: 'Computer Science & Engineering' },
  '08': { code: 'BME', name: 'Biomedical Engineering' },
  '09': { code: 'ECE', name: 'Electronics & Communication Engineering' },
  '10': { code: 'TE', name: 'Textile Engineering' },
  '11': { code: 'IEM', name: 'Industrial Engineering & Management' },
  '12': { code: 'ESE', name: 'Energy Science & Engineering' },
  '13': { code: 'ESE', name: 'Energy Science & Engineering' },
  '14': { code: 'ChE', name: 'Chemical Engineering' },
  '15': { code: 'BME', name: 'Biomedical Engineering' },
  '16': { code: 'Arch', name: 'Architecture' },
  '17': { code: 'URP', name: 'Urban & Regional Planning' },
  '18': { code: 'URP', name: 'Urban & Regional Planning' },
  '19': { code: 'BECM', name: 'Building Engineering & Construction Management' },
  '20': { code: 'BECM', name: 'Building Engineering & Construction Management' },
  '21': { code: 'MSE', name: 'Materials Science & Engineering' },
  '22': { code: 'MSE', name: 'Materials Science & Engineering' },
  '23': { code: 'ChE', name: 'Chemical Engineering' },
  '24': { code: 'ChE', name: 'Chemical Engineering' },
  '25': { code: 'MTE', name: 'Mechatronics Engineering' },
  '26': { code: 'MTE', name: 'Mechatronics Engineering' },
  '27': { code: 'Arch', name: 'Architecture' },
  '28': { code: 'Arch', name: 'Architecture' },
  '29': { code: 'LE', name: 'Leather Engineering' },
  '31': { code: 'TE', name: 'Textile Engineering' }
};

/**
  * Formats a department value into its official acronym (e.g. '07' -> 'CSE', '03' -> 'EEE').
  */
export function formatDept(dept) {
  if (!dept) return 'KUET';
  const str = String(dept).trim();
  
  // If it's already an alphabetic abbreviation (CSE, EEE, CE, etc.), return standard uppercase
  if (/^[A-Za-z]+$/.test(str)) {
    return str.toUpperCase();
  }

  // If numeric code, look up in KUET directory
  const padded = str.padStart(2, '0');
  if (KUET_DEPTS[padded]) {
    return KUET_DEPTS[padded].code;
  }

  return str;
}

/**
  * Returns full department name (e.g. 'Computer Science & Engineering').
  */
export function getDeptFullName(dept) {
  if (!dept) return 'Khulna University of Engineering & Technology';
  const str = String(dept).trim();

  const padded = str.padStart(2, '0');
  if (KUET_DEPTS[padded]) {
    return KUET_DEPTS[padded].name;
  }

  // Reverse search by code
  const upper = str.toUpperCase();
  for (const info of Object.values(KUET_DEPTS)) {
    if (info.code.toUpperCase() === upper) {
      return info.name;
    }
  }

  return str;
}

