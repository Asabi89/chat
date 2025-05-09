/** 
 * This is a minimal config.
 * If you need the full config, get it from here:
 * https://unpkg.com/browse/tailwindcss@latest/stubs/defaultConfig.stub.js
 */
module.exports = {
    content: [
      /**
       * HTML. Paths to Django template files that will contain Tailwind CSS classes.
       */
      /* Templates within theme app (<tailwind_app_name>/templates), e.g. base.html. */
      '../templates/**/*.html',
      
      /* Main templates directory of the project (BASE_DIR/templates). */
      '../../templates/**/*.html',
      
      /* Templates in specific django apps */
      '../../accounts/templates/**/*.html',
      '../../posts/templates/**/*.html',
      '../../stories/templates/**/*.html',
      '../../reels/templates/**/*.html',
      '../../messaging/templates/**/*.html',
      '../../notifications/templates/**/*.html',
      '../../search/templates/**/*.html',
      '../../core/templates/**/*.html',
      
      /* Alternative: All templates in all apps */
      '../../**/templates/**/*.html',
      
      /**
       * JS: If you use Tailwind CSS in JavaScript, uncomment the following lines and make sure
       * patterns match your project structure.
       */
      /* JS 1: Ignore any JavaScript in node_modules folder. */
      '!../../**/node_modules',
      
      /* JS 2: Process all JavaScript files in the project. */
      '../../**/*.js',
      
      /**
       * Python: If you use Tailwind CSS classes in Python, uncomment the following line
       * and make sure the pattern below matches your project structure.
       */
      '../../**/*.py'
    ],
    theme: {
      extend: {
        colors: {
          // Vous pouvez ajouter des couleurs personnalisées ici
        },
        fontFamily: {
          // Vous pouvez ajouter des polices personnalisées ici
        },
      },
    },
    plugins: [
      /**
       * '@tailwindcss/forms' is the forms plugin that provides a minimal styling
       * for forms. If you don't like it or have own styling for forms,
       * comment the line below to disable '@tailwindcss/forms'.
       */
      require('@tailwindcss/forms'),
      require('@tailwindcss/typography'),
      require('@tailwindcss/line-clamp'),
      require('@tailwindcss/aspect-ratio'),
    ],
  }
  